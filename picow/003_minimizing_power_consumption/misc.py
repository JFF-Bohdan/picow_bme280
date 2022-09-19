import machine
import ubinascii


def get_machine_unique_id() -> str:
    return ubinascii.hexlify(machine.unique_id(), ':').decode()

