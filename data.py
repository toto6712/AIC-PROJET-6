#!/bin/python  
###########################################################################
#"""Data.py: Description """            

__author__      = "toto6712"
__version__     = "1.0.1"
___date____     = "22/05/20"

__Modification du code V1.0
Ajout de la variable.ROOTDIR pour exécution du script avec Crontab

##########################################################################

import os
import sys
import re
import subprocess
import tarfile
import datetime
import logging
import boto3
import time
from boto3 import client

##### Variable Initialisation #######
HOMEPATH = 'YOUR WORDPRESS SITE FOLDER'
BACKUP_DATE = datetime.datetime.now().strftime("%d-%m-%Y-%H:%M:%S")
BACKUP_PATH = 'YOUR LOCAL SAVE FOLDER'
BACKUP_NAME =  BACKUP_PATH+'/sauvegarde'+str(BACKUP_DATE)
bucket = "YOUR BUCKET"
ROOTDIR = '/usr/local/bin/'

##### Regex to get back login information to Database #######

def WPregex(HOMEPATH):
    wpconfigfile = os.path.normpath(HOMEPATH +"/wp-config.php")
    with open(wpconfigfile) as fh:
        wpconfigcontent=fh.read()   
    regex_db = r'define\(\s*?\'DB_NAME\'\s*?,\s*?\'(?P<DB>.*?)\'\s*?\);' # Regex to extract db name info
    regex_user = r'define\(\s*?\'DB_USER\'\s*?,\s*?\'(?P<USER>.*?)\'\s*?\);'# Regex to extract db user
    regex_pass = r'define\(\s*?\'DB_PASSWORD\'\s*?,\s*?\'(?P<PASSWORD>.*?)\'\s*?\);'# Regex to extract db password
    regex_host = r'define\(\s*?\'DB_HOST\'\s*?,\s*?\'(?P<HOST>.*?)\'\s*?\);'         # Regex to extract db host
    database = re.search(regex_db,wpconfigcontent).group('DB')
    user = re.search(regex_user,wpconfigcontent).group('USER')
    password = re.search(regex_pass,wpconfigcontent).group('PASSWORD')
    host = re.search(regex_host,wpconfigcontent).group('HOST')
    return {'database':database, 
                'user':user, 
                'password':password, 
                'host':host
                }  

##### Create MariaDB BUMP ########

def WPDBDump(db_details):
    
    USER = db_details['user']
    DBPASSWORD = db_details['password']
    DBHOST = db_details['host']
    DBNAME = db_details['database']
    BACKUP_NAME_SQL = os.path.normpath(os.path.join(BACKUP_PATH+'/sauvegarde'+str(BACKUP_DATE)+'.sql')) # definition name of backup
    cmd = "mysqldump -h{} -u{} -p{} {} > {} ".format(\
        DBHOST, USER, DBPASSWORD, DBNAME, BACKUP_NAME_SQL)
    subprocess.check_output(cmd,shell=True)
    print('Dump OK ..')
    return(BACKUP_NAME_SQL)
        
#######File Compressed ############
def WPBackupTar(HOMEPATH,BACKUP_BDD):
    
    backup_bz2 = tarfile.open(BACKUP_PATH+'/sauvegarde'+str(BACKUP_DATE)+'.tar.bz2','w:bz2') # path of  local save folder (tar.bz2)
    backup_bz2.add(HOMEPATH)
    backup_bz2.add(BACKUP_BDD)
    backup_bz2.close()
    print('zip ok')
    return(backup_bz2)
    
######## File COpie to S3 ########
def CopietoS3(bz2FILE):
   
    cmd = "{}aws s3 cp {} s3://{}/ ".format(\
       ROOTDIR, bz2FILE, bucket) # Shell cmd to updload the file in AWS S3
    subprocess.check_output(cmd,shell=True)
    print('Fichier',bz2FILE,'est uploade')
    return(bz2FILE)
        
#########Verify file in AWS S3############
def veriftoS3(bz2FILE):
    
    s3 = boto3.resource('s3')
    my_bucket = s3.Bucket(bucket)
    file_bucket = s3.ObjectSummary(my_bucket,bz2FILE)
    return (file_bucket)
   
######### Remove LOCAL File in Homepath ############
def Fileremove(bz2FILE,BACKUP_BDD,veriftoS3):
    try:
       veriftoS3
    except NameError:
          print('mauvais fichier copie')
        
    else:
        os.remove(bz2FILE)
        os.remove(BACKUP_BDD)
        print('fichier local supprime')


####### Main Code ################
print ('##################### Backup running...###########################')
####### Check if the path existing ################

if os.path.isdir(HOMEPATH):
    print("Le Dossier",HOMEPATH, "existe")
    print ('##################### Requete regex BDD ###########################')
    DBINFO = WPregex(HOMEPATH)
    print ('##################### Dump BDD ###########################')
    BACKUP_BDD = WPDBDump(DBINFO)
    print ('##################### ZIP des deux fichier ###########################')
    WPBackupTar(HOMEPATH,BACKUP_BDD)
    print ('##################### Copie Vers AWS S3###########################')
    bz2FILE = (BACKUP_PATH+'sauvegarde'+str(BACKUP_DATE)+'.tar.bz2')
    CopietoS3(bz2FILE)
    print ('##################### Verification des fichiers sur AWS ###########################')
    veriftoS3(bz2FILE)
    time.sleep(8) # Waiting time to check the copy before file remove
    remove_on = veriftoS3(bz2FILE)
    print ('##################### Supression fichier Local###########################')
    Fileremove(bz2FILE,BACKUP_BDD,veriftoS3)

else:
    print("dossier", HOMEPATH, "n'existe pas")




    

