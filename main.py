import os
import shutil

from dotenv import load_dotenv

from MORIoTCommand import Command

SYSTEM_ID = 6

COMMAND_ID_SENSOR_EVENT = 0
COMMAND_ID_FILE_CHECK = 1
COMMAND_ID_FILE_REQUEST = 2

INPUT_FOLDER = "unsavedImages"
OUTPUT_FOLDER = "savedImages"


def commandProcess(response, command, length, data=None):
    print("commandProcess command:{},length:{},data:{}".format(command, length, data))
    if command == COMMAND_ID_SENSOR_EVENT:
        print("センサートリガーイベント")
        # response
    elif command == COMMAND_ID_FILE_CHECK:
        try:
            files = os.listdir(INPUT_FOLDER)
            files_file = [f for f in files if os.path.isfile(os.path.join(INPUT_FOLDER, f))]
            print(len(files_file))
            print(files_file)
            if len(files_file) != 0:
                print(files_file[0])
                shutil.move(os.path.join(INPUT_FOLDER, files_file[0]), os.path.join(OUTPUT_FOLDER, files_file[0]))
                file_name = files_file[0].encode()
                response(command, 0, len(file_name), file_name)
            else:
                response(command, 0, 0, None)
        except Exception as e:
            print(e)
            response(command, 0, 0, None)
    elif command == COMMAND_ID_FILE_REQUEST:
        file_index = data[0] * 256 + data[1]
        data_size = data[2] * 256 + data[3]
        print("ReadFile Index:{} DataSize:{}".format(file_index, data_size))
        b = bytearray(data[4:])
        try:
            f = open("./"+OUTPUT_FOLDER+"/" + b.decode(), 'rb')
            if file_index != 0:
                f.read(file_index * data_size)
            file_data = f.read(data_size)
            array = [data[0], data[1], (len(file_data) >> 8) & 0xff, len(file_data) & 0xff]
            array.extend(file_data)
            response(command, 0, len(array), list(array))

        except Exception as e:
            print(e)
            response(command, 1, 0, None)
    else:
        print("一致するコマンドはありません")


def main():
    if not os.path.exists(INPUT_FOLDER):
        os.mkdir(INPUT_FOLDER)
    if not os.path.exists(OUTPUT_FOLDER):
        os.mkdir(OUTPUT_FOLDER)
    port_name = os.getenv('PORT')
    command = Command(port_name, SYSTEM_ID)
    command.read(commandProcess)


if __name__ == '__main__':
    load_dotenv()
    main()
