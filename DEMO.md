# Required Classroom Demo Scenario

## Terminal 1 (Router)
```bash
python -m internet_sim.cli --config config/router_1.json --loss 0.0
```

## Terminal 2 (Student B / Receiver)
```bash
python -m internet_sim.cli --config config/student_b.json --loss 0.0
```

## Terminal 3 (Student A / Sender with packet loss)
```bash
python -m internet_sim.cli --config config/student_a.json --loss 0.35
```

Then from Student A CLI:

```bash
send_message --to 192.168.1.3 --message "Hello Sara" --transport tcp
send_file --to 192.168.1.3 --path examples/class_photo.txt --transport tcp
```

Expected educational observations:
1. DNS resolution (if using domain names)
2. ARP lookup logs
3. TCP handshake logs
4. Router forwarding logs
5. Packet loss and retransmission logs on sender
6. Chunk reception and full file reconstruction on receiver (`received/class_photo.txt`)
