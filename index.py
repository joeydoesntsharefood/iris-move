from concurrent import futures
import grpc
import services_pb2
import services_pb2_grpc
from json import loads
from auth import getServices
from googleapiclient.http import MediaIoBaseDownload
from tqdm import tqdm
import utils

class Service2(services_pb2_grpc.Service2Servicer):
  def ExecuteRoutine(self, request, context):
    service = getServices()['serviceFiles']

    json_string = loads(request.info)
    
    id = ''
    path = []

    res = utils.getFather(service, json_string['id'])

    if 'parents' in res:
      id = res['parents'][0]

      while True:
        res = utils.getFather(service, id)

        if 'parents' in res:
          path += [res['name']]
          id = res['parents'][0]
        else:
          if res['id'] == '0AN6yFIGWA7BwUk9PVA':
            path += ['_2022']
          elif res['id'] == '0AAMenQGp1kxlUk9PVA':
            path += ['_2023']
          break

    result = f'Rotina falho'

    if len(path) != 0:
      path = path[::-1]

      fileName = json_string['name']

      data = {
        'gId': json_string['id'],
        'name': fileName,
        'location': path,
        'size': 0,
        'thumb': ''
      }

      if '06_IMAGENS' in path or '05_IMAGENS' in path:
        DESTINY_FOLDER = '1aomTAi6_QvDlrE8xK-eVHrAobC2vFcDp'
        filePath = f'./downloads/{fileName}'

        data['size'] = utils.downloadFileAndSaveWithProgress(service, data['gId'], './downloads')

        destinyId = utils.createMissingFolders(service, DESTINY_FOLDER, path)

        print(f'Pasta destino: {destinyId}')

        conditional = utils.haveItem(service, destinyId, data['name'], json_string['mimeType'])

        if conditional:
          uploadRes = utils.uploadFileWithProgress(service, filePath, destinyId)

          print(uploadRes)

          utils.saveData(data)

          result = f"Rotina executada com sucesso"
        
        utils.deleteLocalFile(filePath)
      else:
        result = f"Arquivo não se encontra em 06_IMAGENS ou 05_IMAGENS"

    return services_pb2.Response(result=result)

def serve():
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  services_pb2_grpc.add_Service2Servicer_to_server(Service2(), server)
  server.add_insecure_port('[::]:50052')
  server.start()
  server.wait_for_termination()

if __name__ == '__main__':
  serve()
