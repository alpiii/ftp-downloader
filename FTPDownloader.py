from ftplib import FTP
from ftplib import error_perm
import os
import sys


class DownloadError:

    def __init__(self, path, error, fileDirectory):
        """
        Create an instance of this class if an error occures while downloading.
        :param path: File/folder path which reasoned error.
        :param error: Error explanation.
        :param fileDirectory: 'f' for file, 'd' for folder.
        :return: None
        """
        self.path = path
        self.error = error
        self.fileDirectory = fileDirectory


class FTPDownloader:

    def __init__(self):
        """
        FTP Downloader class that establishes connection to the FTP server.
        Downloads all the files in the current folder (and sub folders if specified).
        :return: None
        """
        self.connectionStatus = 0  # 1 connected, 0 not connected
        self.fileCount = 0  # file count downloaded successfully
        self.ftp = None  # FTP class object
        self.errorList = []  # List contains DownloadError class objects.

    def openConnection(self, url, username="", password=""):
        """
        Establishes connection to the FTP server with username and password
        :param url: FTP server address, do not add "ftp://" to beginning.
        :param username: Username for FTP server, leave blank if there is not.
        :param password: Password for FTP server, leave blank if there is not.
        :return: Returns True if connection is established successfully.
        """
        try:
            self.ftp = FTP(url)
            if username == "" or password == "":
                # if FTP server is public, there is no need to use username and password parameters
                self.ftp.login()
            else:
                self.ftp.login(username, password)
            self.connectionStatus = 1  # connection established successfully to the server.
            return True
        except error_perm:
            print sys.exc_info()[1]
            return False
        except:
            print sys.exc_info()[1]
            return False

    def closeConnection(self):
        """
        Closes connection to the FTP server
        :return: None
        """
        if not isinstance(self.ftp, type(None)):
            self.ftp.close()
            self.connectionStatus = 0

    def getFileList(self):
        """
        Gets file list in the current working directory at FTP server.
        :return: File list in current directory.
        """
        files = []

        def dirCallback(line):
            items = line.split()
            if items[0][0] != 'd':  # not 'd' if item is file
                # ninth (index 8) and later elements creates file name
                files.append(' '.join(items[8:]))  # joining with ' ', if file name has blank space

        self.ftp.dir(dirCallback)
        return files

    def getFolderList(self):
        """
        Gets folder list in the current working directory at FTP server.
        :return: Folder list in current directory.
        """
        folders = []

        def dirCallback(line):
            items = line.split()
            if items[0][0] == 'd':  # 'd' if item is folder
                # ninth (index 8) and later elements creates folder name
                folders.append(' '.join(items[8:]))  # joining with ' ', if folder name has blank space

        self.ftp.dir(dirCallback)
        return folders

    def downloadOneFile(self, sourcePath):
        """
        Downloads file to the current OS directory
        :param sourcePath: File path at FTP server
        :return: None
        """
        fileName = os.path.basename(sourcePath)
        try:
            with open(fileName, "wb") as file:
                self.ftp.retrbinary('RETR %s' % sourcePath, file.write)
                self.fileCount += 1  # file downloaded successfully, increasing file count by 1
                print 'File copied : %s' % sourcePath
        except:
            os.remove(fileName)
            self.errorList.append(DownloadError(sourcePath, sys.exc_info()[1], 'f'))
            print 'Error occurred : %s' % sourcePath

    def downloadAllFiles(self, targetPath, sourcePath, subfolders):
        """
        Browse through folders and downloads files in each one.
        :param targetPath: Folder path at local machine to save files
        :param sourcePath: Folder path at FTP server
        :param subfolders: if 'R', this method works recursively and downloads all the files in all directories. if not, files will be downloaded only in 'sourcePath'.
        :return: None
        """
        try:
            self.ftp.cwd(sourcePath)  # changing working directory at FTP server
            os.chdir(targetPath)  # changing working directory in local machine
            files = self.getFileList()
            for file in files:  # download each file in current folder
                if sourcePath == '/':  # if root folder
                    self.downloadOneFile(sourcePath + file)
                else:
                    self.downloadOneFile(sourcePath + '/' + file)
            if subfolders == 'R':
                folders = self.getFolderList()
                for folder in folders:
                    if folder not in [".", ".."]:  # won't work for parent folders
                        if sourcePath == '/':
                            sourcePath = ''
                        os.chdir(targetPath)
                        if not os.path.exists(folder):
                            os.mkdir(folder)
                        if os.name == 'nt':
                            self.downloadAllFiles(targetPath + "\\" + folder, sourcePath + "/" + folder, subfolders)
                        else:
                            self.downloadAllFiles(targetPath + "/" + folder, sourcePath + "/" + folder, subfolders)
        except:
            self.errorList.append(DownloadError(sourcePath, sys.exc_info()[1], 'd'))

    def startDownloading(self, targetPath, sourcePath='/', subfolders='R'):
        """
        Preparing variables to start download.
        :param targetPath: Folder path at local machine to save files
        :param sourcePath: Folder path at FTP server
        :param subfolders: if 'R', this method works recursively and downloads all the files in all directories. if not, files will be downloaded only in 'sourcePath'.
        :return: None
        """
        if self.connectionStatus == 1:
            del self.errorList[:]  # clears error list, it might contain elements from last download operation
            self.fileCount = 0
            self.downloadAllFiles(targetPath, sourcePath, subfolders)
            if self.fileCount == 0:
                print '\nNothing downloaded!\n'
            else:
                print '\n%d files downloaded successfully!\n' % self.fileCount
            return self.errorList
        else:
            print 'A connection to FTP server must be established first.'

if __name__ == "__main__":

    # EXAMPLE
    downloader = FTPDownloader()
    # if you will use username and password, you should change if condition like below.
    # if downloader.openConnection("ftp.cs.brown.edu", "your_username", "your_password"):
    if downloader.openConnection("ftp.cs.brown.edu", "", ""):

        # if you're using Windows, you should send targetPath parameter like that :
        # errorList = downloader.startDownloading('C:\\Users\\HasanAlper\\Desktop\\ftp_downloads', '/u/asf/datasets')
        # if you're not using Windows
        errorList = downloader.startDownloading('/Users/alpiii/Desktop/ftp_downloads', '/u/asf/datasets')
        # if you don't want to download files in sub folders, you can use example below.
        # last parameter must be different from 'R'
        # errorList = downloader.startDownloading('/Users/alpiii/Desktop/ftp_downloads', '/u/asf/datasets', 'A')

        if len(errorList) > 0:
            print '%d error/errors found!' % len(errorList)
            for error in errorList:
                print error.path + ' -> ' + str(error.error)

        downloader.closeConnection()
    else:
        print "Connection couldn't be established."
