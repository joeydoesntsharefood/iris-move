from json import loads
from auth import getServices
from googleapiclient.http import MediaIoBaseDownload
from tqdm import tqdm
from googleapiclient.http import MediaFileUpload
import os
import requests

def findFolderInFolder(service, parentFolderId, folderName):
  query = f"'{parentFolderId}' in parents and mimeType='application/vnd.google-apps.folder' and name='{folderName}' and trashed=false"
    
  results = service.files().list(
    q = query,
    fields = 'files(id,name, parents)',
    supportsAllDrives = True,
    supportsTeamDrives = True,
    includeTeamDriveItems = True,
  ).execute()
    
  if 'files' in results:
    for file in results['files']:
      if file['name'] == folderName:
        return file['id']
    
  return None

def createFolder(service, folderName, parentFolderId):
  fileMetadata = {
    'name': folderName,
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': [parentFolderId]
  }
  file = service.files().create(
    body = fileMetadata,
    supportsAllDrives = True,
    fields = 'id'
  ).execute()
    
  return file['id']

def createMissingFolders(service, rootFolderId, targetPath):
  pathComponents = targetPath
  currentFolderId = rootFolderId
  
  for component in pathComponents:
    existingFolderId = findFolderInFolder(service, currentFolderId, component)
        
    if existingFolderId is None:
      newFolderId = createFolder(service, component, currentFolderId)
      currentFolderId = newFolderId
    else:
      currentFolderId = existingFolderId

  return currentFolderId

def downloadFileAndSaveWithProgress(service, fileId, savePath):
  size = 0

  request = service.files().get_media(
    fileId = fileId,
    supportsAllDrives = True,
  )
  
  fileName = service.files().get(
    fileId = fileId,
    supportsAllDrives = True
  ).execute()['name']
  
  filePath = f"{savePath}/{fileName}"

  response = service.files().get(fileId=fileId, fields='size,name', supportsAllDrives=True).execute()
  file_size = int(response.get('size', 0))

  with open(filePath, 'wb') as f:
    downloader = MediaIoBaseDownload(f, request, chunksize=1024*1024)
    done = False
    with tqdm(
      desc = fileName,
      total = file_size,
      unit = 'B',
      unit_scale = True,
      unit_divisor = 1024
    ) as bar:
      while not done:
        status, done = downloader.next_chunk()
        size = status.total_size
        percentage = status.total_size - bar.n
        bar.update(percentage)

  response = service.files().get(
    fileId = fileId,
    fields = 'id,name,mimeType,modifiedTime,parents',
    supportsAllDrives = True
  ).execute()

  response['localPath'] = filePath
  
  return size

def getFather(service, id):
  req = service.files().get(
    fileId=id,
    supportsAllDrives = True,
    supportsTeamDrives = True,
    fields='parents,name,id,mimeType'
  )

  res = req.execute()

  return res

def uploadFileWithProgress(service, filePath, parentFolderId):
  fileName = os.path.basename(filePath)
  media = MediaFileUpload(filePath, resumable=True)
  
  fileMetadata = {
    'name': fileName,
    'parents': [parentFolderId]
  }

  request = service.files().create(
    body = fileMetadata,
    media_body = media,
    fields = 'id,size',
    supportsAllDrives = True
  )

  with tqdm(
    desc = fileName,
    total = os.path.getsize(filePath),
    unit = 'B',
    unit_scale = True,
    unit_divisor = 1024
  ) as bar:
      response = None
      while response is None:
        status, response = request.next_chunk()
        if status:
          bar.update(status.total_size - bar.n)

  return response

def deleteLocalFile(filePath):
  try:
    os.remove(filePath)
  except Exception as e:
    print("An error occurred:", str(e))

def saveData(data):
  url = 'http://localhost:8080/file'
  
  res = requests.post(url, data)
  
  return res

def haveItem(service, parentFolderId, folderName, mimeType):
  query = f"'{parentFolderId}' in parents and mimeType='{mimeType}' and name='{folderName}' and trashed=false"
    
  results = service.files().list(
    q = query,
    fields = 'files(id,name, parents)',
    supportsAllDrives = True,
    supportsTeamDrives = True,
    includeTeamDriveItems = True,
  ).execute()
    
  if (len(results) == 1): return True
    
  return False