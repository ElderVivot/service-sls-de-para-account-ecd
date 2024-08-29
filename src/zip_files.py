from zipfile import ZipFile


class ZipDataFiles(object):
    def __init__(self, folderTmp) -> None:
        self.__folderTmp = folderTmp
        pass

    def zip(self, filesToZip):
        with ZipFile(f'{self.__folderTmp}/fileszip.zip', 'w') as zip_object:
            for fileZip in filesToZip:
                try:
                    zip_object.write(fileZip, fileZip.split('/')[-1])
                except Exception as e:
                    print('ERROR ZIP FILE', fileZip, e)

    def getZipBuffer(self):
        with open(f'{self.__folderTmp}/fileszip.zip', 'rb') as zip_object:
            return zip_object.read()
