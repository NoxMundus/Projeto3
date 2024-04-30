import pika
import redis
import os
import json
from minio import Minio
from datetime import timedelta
import time

print("Subiu o Consumer")
time.sleep (180)

#Monta o objeto do rabbitMQ e faz o setup da fila
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host="rabbitmq",
     port=5672,
     virtual_host="/",))

channel = connection.channel()
channel.queue_declare(queue="queue_antifraude", arguments={"x-max-priority": 10})
channel.queue_bind(exchange="amq.direct", queue="queue_antifraude", routing_key="antifraudekey")

#monta o objeto do redis
redis_con = redis.Redis(host='redis', port=6379, db=0)

#monta o objeto do minio
minio_conn = Minio(
    endpoint="minio:9000",
    access_key="ricardo",
    secret_key="test1234",
    secure=False,
)

#cria o bucket de antifraude
bucket_name = "bucket-fraudes"

#verifica se o bucket existe
if minio_conn.bucket_exists(bucket_name):
    print(f"Bucket {bucket_name} já existe!")
else:
    minio_conn.make_bucket(bucket_name)
    print("Bucket criado com sucesso!")

#Cria uma politica que permite vc fazer downloads de forma publica do bucket
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::bucket-fraudes/*"
            ]
        }
    ]
}

#Sobe a politica
minio_conn.set_bucket_policy("bucket-fraudes", json.dumps(policy))

#O que acontece quando um mensagem é consumida
def chamado_quando_uma_mensagem_eh_consumida(channel, method_frame, header_frame, body):
    try:
        #Recebe a mensagem e converte para string
        decoded_string = body.decode("utf-8")

        #Deve quebrar a string e fazer com que o _clienteid vire o a chave do cache
        quebramensagem = decoded_string.split(",")

        #Vai colocar que a chave do cache é o id do usuario e subir um cache.
        cache_key = quebramensagem[1]

        #testa se o cache existe, se existir ele vai tentar verificar a fraude
        if(redis_con.exists(cache_key)):
            cache_atual = redis_con.get(cache_key)
            decoded_cache = cache_atual.decode("utf-8")
            quebracache = decoded_cache.split(",")

            #teste se não é uma fraude. Se a location for igual para a mesma _clienteid
            if (quebramensagem[6]==quebracache[6]):
                #como não é uma fraude ele sobrescreve no cashe a ultima entrada do cliente
                redis_con.setex(cache_key, 60, decoded_string)

                #Imprime Validador
                print("-------Validador------" + '\n' + cache_key + "  " + quebramensagem[7])
            
            #se os valores não forem iguais, então é uma fraude.
            else:    
                #Limpa a cache_key deixando só o valor numerico do cliente ID
                cache_key = cache_key.replace("_clienteid': '", "").strip()
                cache_key = cache_key.replace("'", "").strip()

                #Prepara o nome das files e o path
                file_name = cache_key+".txt"
             
                #file_caminho = "/home/ec2-user/Aulas/Cloud/Projeto/Temp/"+file_name
                file_caminho = "/app/"+file_name

                #Cria os arquivos txt
                with open(file_caminho, 'w') as TempFile:
                    TempFile.write(decoded_string)
                    TempFile.close()
                    
                #Sobe para o minio o arquivo txt
                minio_conn.fput_object (
                    bucket_name=bucket_name, 
                    object_name=file_name, 
                    file_path=file_caminho,
                )

                #Imprime Validador
                print("-------Validador------" + '\n' + cache_key + "  " + quebramensagem[7])

                #Cria uma URL de download
                url = minio_conn.get_presigned_url("GET", bucket_name, file_name, expires=timedelta(minutes=30))
                #Altera o minio que está na url para 127.0.0.1 de forma que o PC consiga resolver
                url = url.replace("minio:9000", "projetominio.com")
                #Faz o print da URL fazendo o recorte de tudo que não é preciso nela como a politica tornou o download publico
                print("Alerta de fraude, link abaixo:" + '\n' + url.split("?")[0])

                #Deleta do servidor o arquivo txt para não ficar com lixo
                os.remove(file_caminho)
                

        #Se não existir ele vai incluir o cache
        else:
                redis_con.setex(cache_key, 60, decoded_string)

        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    
    #
    except Exception as e:
        print("Erro: ", e)
        channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=False)
        
#seta que vai coumir da fila do antifraude e que vai ativar o corpo acima para tratar as mensagens
channel.basic_consume(queue="queue_antifraude", on_message_callback=chamado_quando_uma_mensagem_eh_consumida, auto_ack=False)

#Seta o python para começar a receber as mensagens
print("Esperando por mensagens. Para sair pressione CTRL+C")
channel.start_consuming()
