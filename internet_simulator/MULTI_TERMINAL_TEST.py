#!/usr/bin/env python3
"""
Multi-Terminal Test Instructions
This shows you how to run the simulator with multiple terminals
"""

print("""
🎯 MULTI-TERMINAL INTERNET SIMULATOR TEST
========================================

Now you can run nodes in SEPARATE terminals and they will communicate!

📋 STEP-BY-STEP INSTRUCTIONS:

1️⃣  Open Terminal 1 and run:
    python main.py --config configs/user.json

2️⃣  Open Terminal 2 and run:
    python main.py --config configs/ali.json

3️⃣  Open Terminal 3 and run:
    python main.py --config configs/rihaba.json

4️⃣  Now test communication:

📤 FROM USER TERMINAL (Terminal 1):
    send_message 192.168.1.2 "Hello Ali!" udp
    send_message 192.168.1.3 "Hello Rihaba!" udp

📤 FROM ALI TERMINAL (Terminal 2):
    send_message 192.168.1.6 "Hello User!" udp
    send_message 192.168.1.3 "Hi Rihaba!" udp

📤 FROM RIHABA TERMINAL (Terminal 3):
    send_message 192.168.1.6 "Hey User!" udp
    send_message 192.168.1.2 "Hey Ali!" udp

📁 FILE TRANSFER TEST:
    send_file 192.168.1.2 notes.txt tcp
    send_file 192.168.1.6 Ali.png tcp

🔍 CHECK STATUS:
    show_peers
    show_status
    show_files

✅ EXPECTED BEHAVIOR:
- Messages sent from Terminal 1 will APPEAR in Terminal 2/3
- Messages sent from Terminal 2 will APPEAR in Terminal 1/3
- Messages sent from Terminal 3 will APPEAR in Terminal 1/2

📂 FILES CREATED:
- shared_registry.py - Shared node registry
- node_registry.json - Auto-created registry file

🧹 CLEANUP:
When you're done, delete: node_registry.json

🚀 READY TO TEST!
Open 3 terminals and follow the steps above!
""")

# Wait for user to read
input("\nPress Enter to exit...")
