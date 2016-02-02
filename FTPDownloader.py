from ftplib import FTP
from ftplib import error_perm
import os
import sys


class DownloadError:

    def __init__(self, path, error, file_directory):
        """
        Create an instance of this class if an error occures while downloading.
        :param path: File/folder path which reasoned error.
        :param error: Error explanation.
        :param file_directory: 'f' for file, 'd' for folder.
        :return: None
        """
        self.path = path
        self.error = error
        self.file_directory = file_directory


class FTPDownloader:

    def __init__(self):
        """
        FTP Downloader class that establishes connection to the FTP server.
        Downloads all the files in the current folder
        (and sub folders if specified).
        :return: None
        """
        self.connection_status = 0  # 1 connected, 0 not connected
        self.file_count = 0  # file count downloaded successfully
        self.ftp = None  # FTP class object
        self.error_list = []  # List contains DownloadError class objects.

    def open_connection(self, url, user_name="", password=""):
        """
        Establishes connection to the FTP server with username and password
        :param url: FTP server address, do not add "ftp://" to beginning.
        :param user_name: Username for FTP server, leave blank if there is not.
        :param password: Password for FTP server, leave blank if there is not.
        :return: Returns True if connection is established successfully.
        """
        try:
            self.ftp = FTP(url)
            if user_name == "" or password == "":
                # if FTP server is public, there is no need to use username
                # and password parameters
                self.ftp.login()
            else:
                self.ftp.login(user_name, password)
            self.connection_status = 1
            # connection established successfully to the server.
            return True
        except error_perm:
            print sys.exc_info()[1]
            return False
        except:
            print sys.exc_info()[1]
            return False

    def close_connection(self):
        """
        Closes connection to the FTP server
        :return: None
        """
        if not isinstance(self.ftp, type(None)):
            self.ftp.close()
            self.connection_status = 0

    def get_file_list(self):
        """
        Gets file list in the current working directory at FTP server.
        :return: File list in current directory.
        """
        files = []

        def dir_callback(line):
            items = line.split()
            if items[0][0] != 'd':  # not 'd' if item is file
                # ninth (index 8) and later elements creates file name
                # joining with ' ', if file name has blank space
                files.append(' '.join(items[8:]))

        self.ftp.dir(dir_callback)
        return files

    def get_folder_list(self):
        """
        Gets folder list in the current working directory at FTP server.
        :return: Folder list in current directory.
        """
        folders = []

        def dir_callback(line):
            items = line.split()
            if items[0][0] == 'd':  # 'd' if item is folder
                # ninth (index 8) and later elements creates folder name
                # joining with ' ', if folder name has blank space
                folders.append(' '.join(items[8:]))

        self.ftp.dir(dir_callback)
        return folders

    def download_one_file(self, source_path):
        """
        Downloads file to the current OS directory
        :param source_path: File path at FTP server
        :return: None
        """
        file_name = os.path.basename(source_path)
        try:
            with open(file_name, "wb") as file:
                self.ftp.retrbinary('RETR %s' % source_path, file.write)
                # file downloaded successfully, increasing file count by 1
                self.file_count += 1
                print 'File copied : %s' % source_path
        except:
            os.remove(file_name)
            self.error_list.append(DownloadError(source_path,
                                                 sys.exc_info()[1], 'f'))
            print 'Error occurred : %s' % source_path

    def download_all_files(self, target_path, source_path, sub_folders):
        """
        Browse through folders and downloads files in each one.
        :param target_path: Folder path at local machine to save files
        :param source_path: Folder path at FTP server
        :param sub_folders: if 'R', this method works recursively and downloads
        all the files in all directories. if not, files will be downloaded
        only in 'source_path'.
        :return: None
        """
        try:
            # changing working directory at FTP server
            self.ftp.cwd(source_path)
            # changing working directory in local machine
            os.chdir(target_path)
            files = self.get_file_list()
            for file in files:  # download each file in current folder
                if source_path == '/':  # if root folder
                    self.download_one_file(source_path + file)
                else:
                    self.download_one_file(source_path + '/' + file)
            if sub_folders == 'R':
                folders = self.get_folder_list()
                for folder in folders:
                    # won't work for parent folders
                    if folder not in [".", ".."]:
                        if source_path == '/':
                            source_path = ''
                        os.chdir(target_path)
                        if not os.path.exists(folder):
                            os.mkdir(folder)
                        if os.name == 'nt':
                            self.download_all_files(
                                target_path + "\\" + folder,
                                source_path + "/" + folder,
                                sub_folders)
                        else:
                            self.download_all_files(
                                target_path + "/" + folder,
                                source_path + "/" + folder,
                                sub_folders)
        except:
            self.error_list.append(DownloadError(source_path,
                                                 sys.exc_info()[1], 'd'))

    def start_downloading(self, target_path, source_path='/', sub_folders='R'):
        """
        Preparing variables to start download.
        :param target_path: Folder path at local machine to save files
        :param source_path: Folder path at FTP server
        :param sub_folders: if 'R', this method works recursively and downloads
        all the files in all directories. if not, files will be
        downloaded only in 'source_path'.
        :return: None
        """
        if self.connection_status == 1:
            del self.error_list[:]
            # clears error list, it might contain
            # elements from last download operation
            self.file_count = 0
            self.download_all_files(target_path, source_path, sub_folders)
            if self.file_count == 0:
                print '\nNothing downloaded!\n'
            else:
                print '\n%d files downloaded successfully!\n' % self.file_count
            return self.error_list
        else:
            print 'A connection to FTP server must be established first.'

if __name__ == "__main__":

    # EXAMPLE
    downloader = FTPDownloader()
    # if you will use username and password, you should
    # change if condition like below.
    # if downloader.open_connection("ftp.cs.brown.edu",
    #                               "your_username", "your_password"):
    if downloader.open_connection("ftp.cs.brown.edu", "", ""):

        # if you're using Windows, you should
        # send target_path parameter like that :
        # error_list = downloader.start_downloading(
        #     'C:\\Users\\HasanAlper\\Desktop\\ftp_downloads',
        #     '/u/asf/datasets')
        # if you're not using Windows
        error_list = downloader.start_downloading(
            '/Users/alpiii/Desktop/ftp_downloads',
            '/u/asf/datasets')
        # if you don't want to download files in sub folders,
        # you can use example below.
        # last parameter must be different from 'R'
        # error_list = downloader.start_downloading(
        #     '/Users/alpiii/Desktop/ftp_downloads',
        #     '/u/asf/datasets', 'A')

        if len(error_list) > 0:
            print '%d error/errors found!' % len(error_list)
            for error in error_list:
                print error.path + ' -> ' + str(error.error)

        downloader.close_connection()
    else:
        print "Connection couldn't be established."
