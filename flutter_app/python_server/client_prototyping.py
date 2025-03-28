from __future__ import print_function

import numpy as np

import grpc
from server_architecture import hamming_evolve_communication_pb2_grpc
from server_architecture import hamming_evolve_communication_pb2
from HandleEvolveManager import proto_to_numpy

def test_stream(stub):
    arr = np.random.randint(0, 256, size=(12,10,3), dtype=np.int32)  # Replace with actual processing result
    slatArray = [
        hamming_evolve_communication_pb2.Layer3D(layers=[
            hamming_evolve_communication_pb2.Layer2D(rows=[
                hamming_evolve_communication_pb2.Layer1D(values=row.tolist()) for row in layer
            ])
        ]) for layer in arr
    ]
    for update in stub.evolveQuery(hamming_evolve_communication_pb2.EvolveRequest(slatArray=slatArray, parameters={"mutation_rate": "0.05", "crossover": "single_point"})):  # Iterates over streamed responses
        print(f"Progress: {update.progress1}, {update.progress2}, {update.progress3}")

def run():
    with grpc.insecure_channel("localhost:50055") as channel:
        stub = hamming_evolve_communication_pb2_grpc.HandleEvolveStub(channel)
        result = stub.StopProcessing(hamming_evolve_communication_pb2.StopRequest(stop=True))
        np_result = proto_to_numpy(result.handleArray)
        test_stream(stub)

if __name__ == "__main__":
    run()
