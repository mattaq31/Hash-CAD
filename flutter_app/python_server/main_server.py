

def serve():

    DEFAULT_PORT = 50055

    # Get the port number from the command line parameter (if available)
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    HOST = f'localhost:{port}'

    # prepare the gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # add custom class code to the server
    hamming_evolve_communication_pb2_grpc.add_HandleEvolveServicer_to_server(HandleEvolveService(), server)

    # add a health checker system to the server
    health_pb2_grpc.add_HealthServicer_to_server(health.HealthServicer(), server)

    # start server and spin until termination
    server.add_insecure_port(HOST)
    print(f"gRPC server started and listening on {HOST}")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    # attempts to ensure matplotlib remains headless
    import matplotlib

    matplotlib.use('Agg')
    import os
    import multiprocessing as mp

    os.environ["MPLBACKEND"] = "Agg"

    import sys
    from concurrent import futures
    import grpc
    from grpc_health.v1 import health_pb2_grpc
    from grpc_health.v1 import health

    from server_architecture import hamming_evolve_communication_pb2_grpc
    from HandleEvolveManager import HandleEvolveService


    mp.freeze_support()  # needed for PyInstaller/Nuitka on Windows
    serve()
