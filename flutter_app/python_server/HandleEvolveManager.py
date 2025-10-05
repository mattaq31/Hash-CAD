import numpy as np
from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
from server_architecture import hamming_evolve_communication_pb2_grpc, hamming_evolve_communication_pb2

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


class HandleEvolveService(hamming_evolve_communication_pb2_grpc.HandleEvolveServicer):
    def __init__(self):
        self.pause_signal = False
        self.evolve_manager = None

    def evolveQuery(self, request, context):
        print('INITIATING HAMMING EVOLUTION')
        self.pause_signal = False
        is_complete = False
        if self.evolve_manager is None:
            # since Dart system has a flipped x/y representation, need to flip them here first
            slat_array = np.transpose(proto_to_numpy(request.slatArray), (1, 0, 2))
            initial_handle_array = np.transpose(proto_to_numpy(request.handleArray), (1, 0, 2))
            if np.sum(initial_handle_array) == 0:
                initial_handle_array = None
            converted_dict = {key: convert_string_to_float_if_numeric(value) for key, value in dict(request.parameters).items()}
            self.evolve_manager = EvolveManager(slat_array, seed_handle_array=initial_handle_array, **converted_dict)

        for generation in range(self.evolve_manager.current_generation, self.evolve_manager.max_evolution_generations):
            if self.pause_signal:
                break
            self.evolve_manager.single_evolution_step()
            print(f"Yielding generation {generation} - Hamming: {self.evolve_manager.metrics['Corresponding Hamming Distance'][-1]}")

            if len(self.evolve_manager.metrics) > 0:
                if max(self.evolve_manager.metrics['Corresponding Hamming Distance']) >= self.evolve_manager.early_hamming_stop:
                    is_complete = True

            if generation == self.evolve_manager.max_evolution_generations-1:
                is_complete = True

            yield hamming_evolve_communication_pb2.ProgressUpdate(hamming=self.evolve_manager.metrics['Corresponding Hamming Distance'][-1],
                                                                  physics=np.log(self.evolve_manager.metrics['Best (Log) Physics-Based Score'][-1]),
                                                                  isComplete=is_complete)


            if len(self.evolve_manager.metrics) > 0:
                if max(self.evolve_manager.metrics['Corresponding Hamming Distance']) >= self.evolve_manager.early_hamming_stop:
                    break

# TODO: need to implement script export system

    def PauseProcessing(self, request, context):
        self.pause_signal = True
        print('PAUSE TOGGLED')
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
        self.evolve_manager = None
        return hamming_evolve_communication_pb2.FinalResponse(handleArray=handleArray)

    def requestExport(self, request, context):
        print('RECEIVED EXPORT REQUEST')
        self.evolve_manager.export_results(request.folderPath)
        return hamming_evolve_communication_pb2.ExportResponse()
