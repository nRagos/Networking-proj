import os

class Leecher():
    def __init__(self, ip, port, filename):
        self.ip = ip
        self.port = port
        self.filename: str = filename
        
    def getFilename(self):
        return self.filename
    def setFilename(self, filename):
        self.filename = filename

    @staticmethod
    def assemble_file(original_filename, chunks):
        with open(original_filename, 'wb') as output_file:
            for chunk in chunks:
                chunk = os.path.basename(chunk)
                with open(chunk, 'rb') as chunk_file:
                    output_file.write(chunk_file.read())

        print(f"File '{original_filename}' successfully reassembling")

        for c in chunks:
            os.remove(os.path.basename(c))

