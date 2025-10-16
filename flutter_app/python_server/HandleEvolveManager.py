import numpy as np
from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
from server_architecture import hamming_evolve_communication_pb2_grpc, hamming_evolve_communication_pb2
from crisscross.core_functions.megastructures import Megastructure
import threading
import time


def proto_to_numpy(proto_layers):
    """Convert gRPC response into a 3D NumPy array"""
    array_3d = []
    for layer3d in proto_layers:  # Iterate over Layer3D
        array_2d = []
        for layer2d in layer3d.layers:
            for layer1d in layer2d.rows: # Iterate over Layer2D
                array_2d.append(layer1d.values)  # Extract 1D array
        array_3d.append(array_2d)

    return np.array(array_3d, dtype=np.int32)  # Convert to NumPy array


def convert_string_to_float_if_numeric(value):
    try:
        return float(value) if value.replace(".", "", 1).isdigit() else value
    except ValueError:
        return value


def coordinate_map_to_tuples(proto_coordinate_map):
    """
    Convert proto map<string, CoordinateList> to dict[string, list[tuple[int,int]]]
    """

    # x/y flipped for numpy indexing system
    return {
        key: [(coord.y, coord.x) for coord in coord_list.coords]
        for key, coord_list in proto_coordinate_map.items()
    }


class HandleEvolveService(hamming_evolve_communication_pb2_grpc.HandleEvolveServicer):
    def __init__(self):
        self.pause_signal = False
        self.evolve_manager = None
        self._pause_deadline = None
        self._pause_timer = None

    def evolveQuery(self, request, context):
        print('INITIATING ASSEMBLY HANDLE EVOLUTION')
        self.pause_signal = False
        is_complete = False
        if self.evolve_manager is None:
            # since Dart system has a flipped x/y representation, need to flip them here first
            slat_array = np.transpose(proto_to_numpy(request.slatArray), (1, 0, 2))
            initial_handle_array = np.transpose(proto_to_numpy(request.handleArray), (1, 0, 2))
            if np.sum(initial_handle_array) == 0:
                initial_handle_array = None

            converted_dict = {key: convert_string_to_float_if_numeric(value) for key, value in dict(request.parameters).items()}

            # I probably should have used a consistent naming scheme everywhere....
            slat_types_dart = dict(request.slatTypes)
            slat_coordinates_dart = coordinate_map_to_tuples(request.coordinateMap)

            slat_types_python = {}
            slat_coordinates_python = {}
            for s_key, s_value in slat_types_dart.items():
                layer, slat_int_id = s_key.split('-I')
                slat_types_python[(int(layer), int(slat_int_id))] = s_value

            for s_key, s_value in slat_coordinates_dart.items():
                layer, slat_int_id = s_key.split('-I')
                slat_coordinates_python[(int(layer), int(slat_int_id))] = s_value

            main_megastructure = Megastructure(slat_array=slat_array,
                                               slat_coordinate_dict=slat_coordinates_python,
                                               slat_type_dict=slat_types_python,
                                               connection_angle=request.connectionAngle)

            if initial_handle_array is not None:
                main_megastructure.assign_assembly_handles(initial_handle_array)

            self.evolve_manager = EvolveManager(main_megastructure, **converted_dict)

        for generation in range(self.evolve_manager.current_generation, self.evolve_manager.max_evolution_generations):
            if self.pause_signal:
                break
            self.evolve_manager.single_evolution_step()

            print(f"Yielding generation {generation} - Max Valency: {self.evolve_manager.metrics['Corresponding Max Parasitic Valency'][-1]}")

            if len(self.evolve_manager.metrics) > 0:
                if min(self.evolve_manager.metrics['Corresponding Max Parasitic Valency']) <= self.evolve_manager.early_max_valency_stop:
                    is_complete = True

            if generation == self.evolve_manager.max_evolution_generations-1:
                is_complete = True

            yield hamming_evolve_communication_pb2.ProgressUpdate(hamming=self.evolve_manager.metrics['Corresponding Max Parasitic Valency'][-1],
                                                                  physics=self.evolve_manager.metrics['Best Effective Parasitic Valency'][-1],
                                                                  isComplete=is_complete)


            if len(self.evolve_manager.metrics) > 0:
                if max(self.evolve_manager.metrics['Corresponding Max Parasitic Valency']) <= self.evolve_manager.early_max_valency_stop:
                    break

    def _schedule_pause_timeout(self, seconds = 120.0):
        # Cancel any previous timer
        if self._pause_timer is not None:
            try:
                self._pause_timer.cancel()
            except Exception:
                pass
            self._pause_timer = None

        self._pause_deadline = time.monotonic() + seconds

        def _on_timeout():
            # Only kill the pool if we are still paused at the deadline
            if self.pause_signal and self.evolve_manager is not None:
                try:
                    self.evolve_manager.terminate_pool()
                    print('TERMINATED SPAWN POOL DUE TO LONG PAUSE')
                except Exception:
                    pass

        t = threading.Timer(seconds, _on_timeout)
        t.daemon = True
        t.start()
        self._pause_timer = t

    def PauseProcessing(self, request, context):
        self.pause_signal = True
        print('PAUSE TOGGLED')
        self._schedule_pause_timeout(5.0)
        return hamming_evolve_communication_pb2.PauseRequest()

    def StopProcessing(self, request, context):
        self.pause_signal = True
        print('RECEIVED STOP REQUEST')
        # Convert NumPy array to protobuf format
        # since Dart system has a flipped x/y representation, need to flip handle array back here before sending
        handleArray = [
            hamming_evolve_communication_pb2.Layer3D(layers=[
                hamming_evolve_communication_pb2.Layer2D(rows=[
                    hamming_evolve_communication_pb2.Layer1D(values=row.tolist()) for row in layer
                ])
            ]) for layer in np.transpose(self.evolve_manager.handle_array, (1, 0, 2))
        ]
        self.evolve_manager.terminate_pool()
        self.evolve_manager = None
        return hamming_evolve_communication_pb2.FinalResponse(handleArray=handleArray)

    def requestExport(self, request, context):
        print('RECEIVED EXPORT REQUEST')
        self.evolve_manager.export_results(request.folderPath, parameter_export=True)
        return hamming_evolve_communication_pb2.ExportResponse()
