from serial.tools.list_ports import comports


def main():
    print("Available ports")
    ports = comports()
    if not ports:
        print("No ports available")

    for port in ports:
        print(f"{port}")


if __name__ == "__main__":
    main()
