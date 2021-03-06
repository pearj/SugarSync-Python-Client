#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# author: Alexander Straube
# author: Lukas Schreiner
# 
# For editors/contributors: please add an author tag above - 
# for a full list ;-)
#
# For debugging: please use the pudb from
# https://github.com/orsenthil/pudb.git
# because the original does not support python3!

import urllib.request, urllib.error, urllib.parse, mimetypes
from pickle import Unpickler, Pickler
from configparser import SafeConfigParser
from httplib2 import Http, Response
from Printer import Printer
from XMLTextNode import XMLTextNode
from XMLElement import XMLElement
from XMLParser import XMLParser
from SugarSyncInstance import SugarSyncInstance
from SugarSyncNotifier import SugarSyncNotifier
import re, os.path
import datetime
import dateutil.parser

class SugarSync:

    def __init__(self, cmd=False):
        # will be written to config.ini on exit and loaded on startup
        self.username = ''
        self.password = ''
        self.accessKeyId = ''
        self.privateAccessKey = ''
        self.apiURL = ''
        self.token = None
        self.tokenExpire = None
        self.xmlHead = '<?xml version="1.0" encoding="UTF-8" ?>'
        self.config = None
        self.exit = False

        # user info
        self.nickname = ''
        self.salt = ''
        self.quotaLimit = 0
        self.quotaUsage = 0

        #folder
        self.folder = {}

        # Call functions
        self.readConfig()
        self.checkAuth()

        SugarSyncInstance.instance = self

        # only execute menue if cmd is true!
        if cmd:
            self.cmd()

        self.__del__()

    def __del__(self):
        # write config
        print('Saving config...\n')
        self.writeConfig()

    def cmd(self):
        self.exit = False
        while self.exit is False:
            # Menu adding informations: ###: information \n \
            print("\n\n\n \
                   ==== M - E - N - U ====\n\n \
                     0: Exit\n \
                     1: Authenticate\n \
                     2: User info\n \
                     3: load contents collection\n \
                     4: Creating a new folder\n \
                     5: Delete a folder\n \
                     6: Creating a new file\n \
                     7: Delete a file\n \
                     8: Rename a folder\n \
                     9: Rename a file\n \
                    10: Moving a file\n \
                    11: Copy a file\n \
                    12: Upload a file\n \
                    13: Download a file\n \
                    14: Get folder informations\n \
                    15: Get file informations\n \
                    16: Get JPEG-Thumbnail\n \
                    17: Update file informations\n \
                    18: Create public link\n \
                    19: Destroy public link\n \
                    20: Get file history\n \
                    21: Enter Commandline\n \
                    22: Enter saved Commandline\n \
                    23: Start notifier\n \
                    \n \
                   ====  SUGAR  SYNC  ====")
            
            try:
                want = int(input("What do you want?\n"))
            except:
                want = -1

            if want == 0:
                print("\nExiting...\n")
                self.exit = True
            elif want == 1:
                print("\nAuthenticating...\n")
                self.auth()
            elif want == 2:
                print("\nUser info...\n")
                self.getUser()
            elif want == 3:
                print('\nCollecting all files...\n')
                self.getAllFilesCollection()
            elif want == 4:
                print('\nCreating a new folder...\n')
                # we need path:
                path = input('Folder path: ')
                newfolder = input('Foldername: ')

                self.createFolder(path, newfolder)
            elif want == 5:
                print('\nDeleting a folder...\n')
                # we need the folder id
                foldername = input('Folder ID: ')
                
                self.deleteFolder(foldername)
            elif want == 6:
                print('\nCreating a new file...\n')
                # we need path:
                path = input('Folder path: ')
                # we need filename
                newfile = input('Filename: ')
                # and last but not least: media type
                media = input('MediaType (ex. text/plain, image/jpeg): ')

                self.createFile(path, newfile, media)
            elif want == 7:
                print('\nDeleting a file...\n')
                # we need the file id
                filename = input('File ID: ')
                
                self.deleteFile(filename)
            elif want == 8:
                print('\nRenaming a folder...\n')
                # we need folder
                path = input('Folder: ')
                # we need new name
                name = input('New folder name: ')

                self.renameFolder(path, name)
            elif want == 9:
                print('\nRenaming a file...\n')
                # we need folder
                path = input('File: ')
                # we need new name
                name = input('New file name: ')

                self.renameFile(path, name)
            elif want == 10:
                print('\nMoving a file...\n')
                # we need the file
                filename = input('File: ')
                # we need the new path
                path = input('New path (collection): ')

                self.moveFile(filename, path)
            elif want == 11:
                print('\nCopy a file...\n')
                # we need the source
                source = input('Source file: ')
                # we need the target folder
                target = input('Target folder: ')
                # we need the name
                name = input('Name (in future on blank it will receive actual name): ')

                self.copyFile(source, target, name)
            elif want == 12:
                print('\nUploading a file...\n')
                # we need the filename
                filename = input('File to be uploaded (local!): ')
                # remote file
                filename = input('File in SugarSync: ')

                self.uploadFile(filename, filename)
            elif want == 13:
                print('\nDownloading a file...\n')
                # we need the file
                filename = input('File (remote): ')
                # save to?
                saveto = input('Save to (with filename): ')

                self.getFile(filename, saveto)
            elif want == 14:
                print('\nRetrieving folder informations...\n')
                # we need folder id
                folder = input('Folder: ')

                SugarSync.getFolderInfo(folder)
            elif want == 15:
                print('\nRetrieving file informations...\n')
                # we need file id
                filename = input('File: ')

                SugarSync.getFileInfo(filename)
            elif want == 16:
                print('\nRetrieving file thumbnail...\n')
                print('For your information: actual it only works if square: 1')

                image = input('Image: ')
                saveto = input('Save to: ')

                pxmax = input('Width: ')
                pymax = input('Height: ')
                square = input('Square (0 => No, 1 => Yes): ')
                rotate = input('Rotate (number of clockwise rotations): ')

                self.getThumbnail(image, saveto, pxmax, pymax, square, rotate)
            elif want == 17:
                print('\nSet new file informations...\n')
                
                filename = input('File: ')
                newname = input('New name (or leave blank): ')
                mediatype = input('Media type (or leave blank): ')
                parent = input('Parent (or leave blank): ')

                self.updateFile(filename, newname, mediatype, parent)
            elif want == 18:
                print('\nCreate public link for file...\n')

                filename = input('File: ')

                self.setPublicLink(filename, True)
            elif want == 19:
                print('\nDestroy public link for file...\n')

                filename = input('File: ')

                self.setPublicLink(filename, False)
            elif want == 20:
                print('\nGet file version history...\n')

                filename = input('File: ')

                SugarSync.getFileHistory(filename)
            elif want == 21:
                print('\nWelcome to SugarSync-Python-Client Commandline...\n')

                self.startCommandline()
            elif want == 22:
                print('\nWelcome to SugarSync-Python-Client Commandline...\n')

                self.startSavedCommandline()
            elif want == 23:
                self.startNotifier()
            else:
                print("\n\nWRONG input - Try again!\n\n")

    
    def readConfig(self):
        self.config = SafeConfigParser()
        self.config.read(['config.ini'])

        self.username = self.config.get('user', 'username')
        self.password = self.config.get('user', 'password')
        self.nickname = self.config.get('user', 'nickname')
        self.accessKeyId = self.config.get('connection', 'accessKeyId')
        self.privateAccessKey = self.config.get('connection', 'privateAccessKey')
        self.apiURL = self.config.get('connection', 'url')

        self.token = self.config.get('auth', 'token')
        self.tokenExpire = self.config.get('auth', 'tokenExpire')
        # user
        self.quotaLimit = self.config.get('quota', 'limit')
        self.quotaUsage = self.config.get('quota', 'usage')
        
        # folder
        for k,v in self.config.items('folder'):
            self.folder[k] = v


    def writeConfig(self):
        self.config.set('user', 'username', str(self.username))
        self.config.set('user', 'password', str(self.password))
        self.config.set('user', 'nickname', str(self.nickname))
        self.config.set('connection', 'accessKeyId', str(self.accessKeyId))
        self.config.set('connection', 'privateAccessKey', str(self.privateAccessKey))
        self.config.set('connection', 'url', str(self.apiURL))
        self.config.set('auth', 'token', str(self.token))
        self.config.set('auth', 'tokenExpire', str(self.tokenExpire))
        self.config.set('quota', 'limit', str(self.quotaLimit))
        self.config.set('quota', 'usage', str(self.quotaUsage))

        for k,v in self.folder.items():
            self.config.set('folder', str(k), str(v))

        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def sendRequest(self, path, data = {}, token = True, post = True, headers = {}):
        response = None
        request = None

        if post:
            headers['Content-Type'] = 'application/xml; charset=UTF-8'
        if token:
            headers['Authorization'] = '%s' % self.token

        try:
            if post:
                request = urllib.request.Request(self.apiURL+path, data.encode('utf8'))
            elif len(data) == 0:
                request = urllib.request.Request(self.apiURL+path)
            else:
                print('I have data in sendRequest but i don\'t know what i should do with it :D')

            if request is not None:
                for k,v in headers.items():
                    request.add_header(k, v)

                response = urllib.request.urlopen(request)

        except urllib.error.HTTPError as e:
            print('Error while requesting API call: %s (%s)' % (e.msg, e.code))
            print('URL: %s' % (self.apiURL+path))
        except urllib.error.URLError as e:
            print('Error while requesting API call: %s' % (e.reason))
            
        return response
 
    def sendRequestPut(self, url, data = {}, ctype = 'application/xml; charset=UTF-8', length = None, binary = False):
        response = None

        if binary is False:
            data = data.encode('utf8')

        headers = {'Authorization': self.token}
        
        if type is not None:
            headers['Content-Type'] = '%s' % ctype

        if length is not None:
            headers['Content-Length'] = '%s' % length

        h = Http(disable_ssl_certificate_validation=True)
        resp, content = h.request(self.apiURL+url, 'PUT', data, headers)

        if content is not None:
            content = content.decode('utf8')
        
        return (resp, content)

    def sendRequestDelete(self, url):
        response = None
        
        headers = {'Authorization': self.token}
        h = Http(disable_ssl_certificate_validation=True)
        resp, content = h.request(self.apiURL+url, 'DELETE', None, headers)

        if content is not None:
            content = content.decode('utf8')

        return (resp, content)

    @staticmethod
    def parseDate(date):
        d1 = dateutil.parser.parse(date)
        d1 = d1.astimezone(dateutil.tz.tzutc())
        d1 = d1.replace(tzinfo=None)

        return d1

    def checkAuth(self):
        # check whether token is expired or not!
        date = SugarSync.parseDate(self.tokenExpire)
        date2 = datetime.datetime.utcnow()

        # compare: if date <= date2: self.auth, else: nothing!
        if date != None:
            if date <= date2:
                self.auth()
                return False
            else:
                return True
        else:
            return True


    def auth(self):
        data = XMLElement('authRequest')
        data.setHead(self.xmlHead)

        data.addChild(XMLElement('username').addChild(XMLTextNode(self.username)))
        data.addChild(XMLElement('password').addChild(XMLTextNode(self.password)))
        data.addChild(XMLElement('accessKeyId').addChild(XMLTextNode(self.accessKeyId)))
        data.addChild(XMLElement('privateAccessKey').addChild(XMLTextNode(self.privateAccessKey)))
        
        response = self.sendRequest('/authorization', data.toString(), False)
        if response is not None:
            info = response.info()
            self.token = info['Location']
            resp = XMLElement.parse(response.read().decode('utf8'))
            self.tokenExpire = resp.expiration
            # get the user info
            self.getUser()

    def addElementToDatabase(self, file, location):
        # this is for sync. TODO: implment element adding to database.
        pass

    def startSavedCommandline(self):
        from SugarSyncShell import SugarSyncShell
        path = None
        if os.path.isfile('syncdata.bin'):
            with open('syncdata.bin', 'rb') as f:
                path = Unpickler(f).load()
        else:
            print('File not found. Session saved?')

        if path == None:
            self.startCommandline()
        else:
            ssh = SugarSyncShell(self, path[0])
            ssh.path = path
        

    def startCommandline(self):
        from SugarSyncCollection import SugarSyncCollection
        from SugarSyncShell import SugarSyncShell

        # starting with folder->syncfolders
        startdir = self.config.get('folder', 'syncfolders')
        startdir = startdir[25:] # its temp. We should implement this in an other way.
        
        # startdir will be an object. so create it here.
        startdir = SugarSyncCollection(startdir)

        # we have the problem, that we start within an collection!
        # so we can't use getFileInfo.

        ssh = SugarSyncShell(self, startdir)

    def createFile(self, path, filename, media):
        location = None
        data = XMLElement('file')
        data.setHead(self.xmlHead)

        data.addChild(XMLElement('displayName').addChild(XMLTextNode(filename)))
        data.addChild(XMLElement('mediaType').addChild(XMLTextNode(media)))

        response = self.sendRequest('/folder/%s' % path, data.toString(), False)
        if response is not None:
            info = response.info()
            code = response.getcode()
            location = info['Location']
            if code == 201:
                self.addElementToDatabase('%s/%s' % (path, filename), location)
                print('File created with success. Location: %s' % location)
            else:
                print('File could not be deleted (Code: %s)!' % (code))

        return location

    def renameFile(self, path, newname):
        data = XMLElement('file')
        data.setHead(self.xmlHead)

        data.addChild(XMLElement('displayName').addChild(XMLTextNode(newname)))

        resp, content = self.sendRequestPut('/file/%s' % path, data.toString())

        if resp is not None:
            if int(resp['status']) == 200:
                print('File renamed.')
            else:
                print('File could not be renamed (Code: %s)!' % (resp['status']))

    def moveFile(self, file, newpath):
        data = XMLElement('file')
        data.setHead(self.xmlHead)
        newpath = self.apiURL + '/folder/%s' % newpath

        data.addChild(XMLElement('parent').addChild(XMLTextNode(newpath)))

        resp, content = self.sendRequestPut('/file/%s' % file, data.toString())
        
        if resp is not None:
            if int(resp['status']) == 200:
                print('File moved.')
            else:
                print('File could not be moved (Code: %s)!' % (resp['status']))

    @staticmethod
    def getFileInfo(filename, absolut=False): # filename => file id
        sync = SugarSyncInstance.instance

        if absolut is False:
            filename = '/file/' + filename

        resp = sync.sendRequest(filename, post=False)
        respData = None

        if resp is not None:
            if int(resp.status) == 200:
                print('Received successful.')
                # data.. but in which method?
                data = resp.read().decode('utf8')
                respData = XMLElement.parse(data)

            else:
                print('File informations could not be retrieved. (Code: %s)' % resp.status)

        else:
            print('Could not retrieve file informations.')
        
        return respData
    
    def getFile(self, filename, saveto):
        response = self.sendRequest('/file/%s/data' % filename, {}, True, False)

        if response is not False:
            info = response.info()
            code = response.getcode()
            data = response.read()
            try:
                data = data.decode('utf8')
            except UnicodeDecodeError: 
                print('Save as not utf-8 file')

            if code == 200:
                # now write
                if isinstance(data, str):
                    try:
                        d = open(saveto, 'w')
                        d.write(data)
                        d.close()

                        print('File downloaded and saved.')
                    except Exception as e:
                        print('File downloaded but not saved.')
                        print(type(e))
                else:
                    try:
                        d = open(saveto, 'wb')
                        d.write(data)
                        d.close()

                        print('File downloaded and saved.')
                    except Exception as e:
                        print('File downloaded but not saved.')
                        print(type(e))
            else:
                print('File could not be downloaded (Code: %s)!' % (code))

    @staticmethod
    def getFileHistory(filename):
        from SugarSyncFile import SugarSyncFile
        sync = SugarSyncInstance.instance

        response = sync.sendRequest('/file/%s/version' % filename, {}, True, False)
        files = None

        if response is not False and response is not None:
            info = response.info()
            code = response.getcode()
            data = XMLElement.parse(response.read().decode('utf8'))

            # We will parse into SugarSyncFile and then return an dict maybe sorted after
            # lastModified
            if code == 200 and data is not None:
                files = []
                for fv in data.childs:
                    version = SugarSyncFile(fv.ref)
                    version.setSize(fv.size)
                    version.setMediaType(str(fv.mediaType))
                    version.setPresentOnServer(str(fv.presentOnServer))
                    version.setLastModified(str(fv.lastModified))

                    files.append(version)

            if code == 200:
                print('Got file history successfully.')
            else:
                print('Error on getting history (Code: %s)!' % (code))

        else:
            print('Request failed.')

        return files


    def getThumbnail(self, image, saveto, xmax, ymax, square = 1, rotate=0):
        header = {'Accept': 'image/jpeg; pxmax=%s; pymax=%s; sq=%s; r=%s;' % (xmax, ymax, square, rotate)}
        response = self.sendRequest('/file/%s/data' % image, {}, True, False, header)

        if response is not False and response is not None:
            info = response.info()
            code = response.getcode()
            data = response.read()

            if code == 200:
                try:
                    d = open(saveto, 'wb')
                    d.write(data)
                    d.close()

                    print('Thumbnail downloaded and saved.')
                except:
                    print('Thumbnail downloaded but not saved.')
            else:
                print('Thumbnail could not be downloaded (Code: %s)!' % (code))
        else:
            print('Thumbnail could not be downloaded in cause of an None Object!')


    def uploadFile(self, lfile, filename, create=False):
        """ filename can be a file id (on create=False) or an target folder with name! """
        # we will read file
        data = None
        binary = False
        mimetype = None
        length = None
        
        try:
            d = open(lfile, 'r')
            data = d.read()
        except:
            try:
                d = open(lfile, 'rb')
                data = d.read()
                binary = True
            except:
                print('ERROR: File could not be read!')

        if data is not None:
            # we have load all so we can close it
            d.close()

            # mimetype
            mimetypes.init()
            mimetype = mimetypes.guess_type(lfile)
            if mimetype[0] is not None:
                mimetype = mimetype[0]
            else:
                mimetype = 'text/plain'
                           
            # length
            length = os.path.getsize(lfile)

            # lets create it ;-)
            if create:
                fsplit = filename.split('/')
                if len(fsplit) == 2:
                    location = self.createFile(fsplit[0], fsplit[1], mimetype)
                    if location is not None:
                        location = location.split('/')
                        filename = location[len(location)-1]
                    else:
                        print('File could not be created!')
                        return None
                else:
                    print('Wrong parameter!')
                    return None

            resp, content = self.sendRequestPut('/file/%s/data' % filename, data, mimetype, length, True)

            if resp is not None:
                if int(resp['status']) == 204:
                    print('File uploaded.')
                else:
                    print('File could not be uploaded (Code: %s)!' % (resp['status']))

    def updateFile(self, filename, name = '', mediaType = '', parent = ''):
        resp = None
        content = None

        if parent != '':
            parent = self.apiURL + '/folder/%s' % parent

        if parent != '' or name != '' or mediaType != '':
            data = XMLElement('file')
            data.setHead(self.xmlHead)

            if name != '':
                data.addChild(XMLElement('displayName').addChild(XMLTextNode(name)))

            if mediaType != '':
                data.addChild(XMLElement('mediaType').addChild(XMLTextNode(mediaType)))

            if parent != '':
                data.addChild(XMLElement('parent').addChild(XMLTextNode(parent)))

            resp, content = self.sendRequestPut('/file/%s' % filename, data.toString())

            if resp is not None:
                if int(resp['status']) == 200:
                    content = XMLElement.parse(content) # here are the file infos ;-)

                    print('File Information updated')
                else:
                    print('File information could not be updated (Code: %s)!' % (resp['status']))
        else:
            print('There is nothing to change O_o')

    def copyFile(self, source, target, name):
        print(source, target, name)
        data = XMLElement('fileCopy')
        data.setHead(self.xmlHead)
        data.setAttribute('source', self.apiURL+'/file/'+source)
        data.addChild(XMLElement('displayName').addChild(XMLTextNode(name)))

        response = self.sendRequest('/folder/%s' % target, data.toString())
        
        if response is not None:
            info = response.info()
            code = response.getcode()
            location = info['Location']

            if code == 201:
                self.addElementToDatabase('%s/%s' % (target, name), location)
                print('File copied with sucess. Location: %s' % location)
                return True
            else:
                print('File could not be copied (Code: %s)!' % (code))

            return False

    def deleteFile(self, filename):
        resp, content = self.sendRequestDelete('/file/'+filename)   

        if resp is not None:
            if int(resp['status']) == 204:
                print('File deleted.')
            else:
                print('File could not be deleted (Code: %s)!' % (resp['status']))

    def setPublicLink(self, filename, create=True):
        resp = None
        content = None

        data = XMLElement('file')
        data.setHead(self.xmlHead)
        
        elm = XMLElement('publicLink')
        if create:
            elm.setAttribute('enabled', 'true')
        else:
            elm.setAttribute('enabled', 'false')

        data.addChild(elm)

        resp, content = self.sendRequestPut('/file/%s' % filename, data.toString())

        if resp is not None:
            if int(resp['status']) == 200:
                content = XMLElement.parse(content)
                if create:
                    print('Created public link: %s' % content.publicLink)
                else: 
                    print('Public link destroyed successful.')
            else:
                print('Could not create/destroy public link (Code: %s).' % resp['status'])
        else:
            print('Could not create/destroy public link (request failed).')

    def createFolder(self, path, foldername):
        data = XMLElement('folder')
        data.setHead(self.xmlHead)

        data.addChild(XMLElement('displayName').addChild(XMLTextNode(foldername)))

        response = self.sendRequest('/folder/%s' % path, data.toString())

        if response is not None:
            info = response.info()
            code = response.getcode()
            location = info['Location']
            if code == 201:
                self.addElementToDatabase('%s/%s' % (path, foldername), location)
                print('Folder created with success. Location: %s' % location)
            else:
                print('Folder could not be deleted (Code: %s)!' % (code))

    def renameFolder(self, path, newfolder):
        data = XMLElement('folder')
        data.setHead(self.xmlHead)

        data.addChild(XMLElement('displayName').addChild(XMLTextNode(newfolder)))

        resp, content = self.sendRequestPut('/folder/%s' % path, data.toString())

        if resp is not None:
            if int(resp['status']) == 204:
                print('Folder renamed.')
            else:
                print('Folder could not be renamed (Code: %s)!' % (resp['status']))

    @staticmethod
    def getFolderInfo(foldername): # foldername is the id
        sync = SugarSyncInstance.instance

        resp = sync.sendRequest('/folder/'+foldername, post=False)
        respData = None

        if resp is not None:
            if int(resp.status) == 200:
                print('Received successful.')
                # data.. but in which method?
                data = resp.read().decode('utf8')
                respData = XMLElement.parse(data)

            else:
                print('Folder Informations could not be retrieved. (Code: %s)' % resp.status)

        else:
            print('Could not retrieve folder informations.')
        
        return respData

    def deleteFolder(self, foldername):
        resp, content = self.sendRequestDelete('/folder/'+foldername)   

        if resp is not None:
            if int(resp['status']) == 204:
                print('Folder deleted.')
            else:
                print('Folder could not be deleted (Code: %s)!' % (resp['status']))

    def getUser(self): 
        response = self.sendRequest('/user', {}, True, False)

        if response is not None:
            resp = XMLElement.parse(response.read().decode('utf8'))
            self.username = str(resp.username)
            self.nickname = str(resp.nickname)
            self.quotaLimit = resp.quota.limit
            self.quotaUsage = resp.quota.usage
            print("Username:\t", self.username)
            print("Nickname:\t", self.nickname)
            print("Space Limit:\t", self.quotaLimit, "Bytes")
            print("Space Used:\t", self.quotaUsage, "Bytes\n")

    def getWorkspace(self, pcid):
        pass

    @staticmethod
    def getCollectionContentInfo(link, typ = 'all', start = 0, maxnumber = 500):
        sync = SugarSyncInstance.instance

        if typ in ['file','folder']:
            typ = '&type=%s' % typ
        else:
            typ = ''
        
        if link[:1] != '/':
            link = '/'+link

        response = sync.sendRequest(link+'?start=%i&max=%i%s' % (start,maxnumber,typ), {}, True, False)

        if response is not None:
            raw_data = response.read().decode('utf8')
            #print(raw_data)
            #data = XMLElement.parse(raw_data)
            data = XMLParser.parse(raw_data)

            return data

        else:
            return None

    @staticmethod
    def getFolderContents(link, typ = 'all', start = 0, maxnumber = 500):
        sync = SugarSyncInstance.instance

        if typ in ['file','folder']:
            typ = '&type=%s' % typ
        else:
            typ = ''
          
        if link[:1] != '/':
            link = '/'+link

        link = '/folder' + link

        response = sync.sendRequest(link+'/contents?start=%i&max=%i%s' % (start,maxnumber,typ), {}, True, False)
        if response is not None:
            raw_data = response.read().decode('utf8')
            data = XMLParser.parse(raw_data)

            return data
        else:
            return None

    def getAllFilesCollection(self):
        response = self.sendRequest('/user', {}, True, False)
        
        if response is not None:
            data = XMLElement.parse(response.read().decode('utf8'))
            self.quotaLimit = data.quota.limit
            self.quotaUsage = data.quota.usage
        
            self.folder['workspaces'] = data.workspaces
            self.folder['syncfolders'] = data.syncfolders
            self.folder['deleted'] = data.deleted
            self.folder['magicBriefcase'] = data.magicBriefcase
            self.folder['webArchive'] = data.webArchive
            self.folder['mobilePhotos'] = data.mobilePhotos
            self.folder['albums'] = data.albums
            self.folder['recentactivities'] = data.recentActivities
            self.folder['receivedshares'] = data.receivedShares
            self.folder['publiclinks'] = data.publicLinks
        
            print("Data loaded! \n\n")

    def startNotifier(self):
        # in future we want to save the added notifications on startup.
        snotifier = SugarSyncNotifier(self)
        snotifier.startNotifier()
        # that's it ;-)
        path = None
        try:
            while True:
                path = input('Give me a local path for watching...\n')
                print('\n\nCheck whether path exists or not...')
                if os.path.exists(path):
                    print('\nCongrats! The path exists. Start watching ;-)\n\n')
                    snotifier.addNotifierPath(os.path.abspath(path), None)
                else:
                    print('\nFoo! The path does not exist. Try again!\n\n')
        except KeyboardInterrupt as ke:
            print('You\'ve stopped!')

        self.stopNotifier()

    def stopNotifier(self):
        snotifier = SugarSyncInstance.notifier
        snotifier.stopNotifier()

if __name__ == "__main__":
    ss = SugarSync(True)
