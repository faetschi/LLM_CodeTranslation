import socket

try:
    print("Resolving 'rabbitmq'...")
    ip = socket.gethostbyname("rabbitmq")
    print(f"✅ 'rabbitmq' resolves to: {ip}")
    print("Attempting AMQP connection on port 5672...")
    s = socket.socket()
    s.settimeout(3)
    s.connect((ip, 5672))
    print("✅ Successfully connected to RabbitMQ on port 5672!")
    s.close()
except Exception as e:
    print(f"❌ Connection error: {e}")
