import pyvisa
import time
import numpy as np

def benchmark_oscilloscope():
    rm = pyvisa.ResourceManager()
    scope = rm.open_resource('USB0::0x2A8D::0x039B::CN63261167::INSTR')
    
    # Massive timeout because ASCII is incredibly slow
    scope.timeout = 30000 
    
    scope.write(":DIGitize CHANnel1")
    scope.write(":WAVeform:SOURce CHANnel1")
    
    try:
        points = int(scope.query(":WAVeform:POINts?"))
    except:
        scope.write(":WAVeform:FORMat BYTE")
        temp_data = scope.query_binary_values(":WAVeform:DATA?", datatype='s', is_big_endian=True)
        points = len(temp_data)

    print(f"--- Benchmarking Oscilloscope Transfer ---")
    print(f"Waveform size: {points} points\n")

    # Use different iteration counts because ASCII is so slow
    ascii_iterations = 5
    byte_iterations = 30

    # ==========================================
    # 1. ASCII FORMAT BENCHMARK
    # ==========================================
    print(f"Running ASCII Benchmark ({ascii_iterations} iterations)...")
    scope.write(":WAVeform:FORMat ASCii")
    
    ascii_times = []
    for i in range(ascii_iterations):
        print(f"  ASCII Iteration {i+1}/{ascii_iterations} - waiting for scope...")
        start_time = time.perf_counter()
        
        raw_str = scope.query(":WAVeform:DATA?")
        
        if raw_str.startswith('#'):
            num_digits = int(raw_str[1])
            header_length = 2 + num_digits
            raw_str = raw_str[header_length:]
            
        data_ascii = np.fromstring(raw_str, dtype=float, sep=',')
        
        end_time = time.perf_counter()
        ascii_times.append(end_time - start_time)
        
    avg_ascii_latency = np.mean(ascii_times)
    ascii_throughput = (points / avg_ascii_latency) / 1000  

    # ==========================================
    # 2. BYTE (BINARY) FORMAT BENCHMARK
    # ==========================================
    print(f"\nRunning BYTE Benchmark ({byte_iterations} iterations)...")
    scope.write(":WAVeform:FORMat BYTE")
    
    byte_times = []
    for i in range(byte_iterations):
        if (i+1) % 10 == 0:
            print(f"  BYTE Iteration {i+1}/{byte_iterations}...")
            
        start_time = time.perf_counter()
        data_byte = scope.query_binary_values(":WAVeform:DATA?", datatype='s', is_big_endian=True)
        end_time = time.perf_counter()
        
        byte_times.append(end_time - start_time)

    avg_byte_latency = np.mean(byte_times)
    byte_throughput = (points / avg_byte_latency) / 1000  

    # ==========================================
    # 3. REPORTING
    # ==========================================
    print("\n" + "="*45)
    print("                 RESULTS                 ")
    print("="*45)
    print(f"ASCII Latency:       {avg_ascii_latency:.4f} seconds")
    print(f"ASCII Throughput:    {ascii_throughput:.2f} kSamples/s")
    print("-" * 45)
    print(f"BYTE Latency:        {avg_byte_latency:.4f} seconds")
    print(f"BYTE Throughput:     {byte_throughput:.2f} kSamples/s")
    print("-" * 45)
    
    speedup = avg_ascii_latency / avg_byte_latency
    print(f"CONCLUSION: BYTE format is {speedup:.2f}x faster than ASCII")
    print("="*45)

    scope.close()

if __name__ == "__main__":
    benchmark_oscilloscope()