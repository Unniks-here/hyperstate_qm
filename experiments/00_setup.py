from qiskit_ibm_runtime import QiskitRuntimeService
import sys

# !!! IMPORTANT: Replace this string with your actual IBM Quantum API Token !!!
API_TOKEN = "i1uBSca2dwMnoKlWBWeYfiAWub5TOv8rsnEzHQo60uPl"

if API_TOKEN == "PASTE_YOUR_IBM_TOKEN_HERE":
    print("ERROR: You must replace 'PASTE_YOUR_IBM_TOKEN_HERE' with your actual API token.")
    print("Get it from: https://quantum.ibm.com/account")
    sys.exit(1)

print("1. Attempting to save account...")
try:
    # This saves your account to your local machine.
    # The error indicated your SDK expects 'ibm_quantum_platform' instead of 'ibm_quantum'
    QiskitRuntimeService.save_account(
        channel="ibm_quantum_platform", 
        token=API_TOKEN, 
        overwrite=True
    )
    print("Success! Account saved locally.")
    
    print("2. Testing connection to IBM Quantum (this may take a moment)...")
    # Test the load explicitly using the new channel name
    service = QiskitRuntimeService(channel="ibm_quantum_platform")
    print(f"Connected to service: {service.channel}")
    print("You are ready to run the experiment script.")
    
except Exception as e:
    print(f"\nSetup failed! Error details:")
    print(e)
