#!/usr/bin/python2.6
#conding=utf-8

import MySQLdb
import os,sys

class CMysql:
    def __init__(self,host,port,user,pwd,db,charset):
        self.host = host
        self.port = port
        self.user = user
        self.password  = pwd
        self.db   = db
        self.charset   = charset
        self.UPDATE_TIMES=0
        self.conn = None
        self.cur = None
        try:
            self.conn=MySQLdb.connect(host=self.host,user=self.user,passwd=self.password,db=self.db,port=self.port)
            self.conn.set_character_set(self.charset)  
            self.cur=self.conn.cursor()  
        except MySQLdb.Error as e:
            print("Mysql Error %d: %s" % (e.args[0], e.args[1]))
    
    def connect(self):
        try:
            self.conn=MySQLdb.connect(host=self.host,user=self.user,passwd=self.password,db=self.db,port=self.port) 
            self.conn.set_character_set(self.charset)  
            self.cur=self.conn.cursor()  
        except MySQLdb.Error as e:
            print("Mysql Error %d: %s" % (e.args[0], e.args[1]))
        
    def selectDb(self,db):
        try:
            self.conn.select_db(db)
        except MySQLdb.Error as e:
            print("Mysql Error %d: %s" % (e.args[0], e.args[1]))

    def query(self,sql):
        try:
           n=self.cur.execute(sql)
           return n
        except MySQLdb.Error as e:
           print("Mysql Error:%s\nSQL:%s" %(e ,sql.encode("utf8")))
	   try:
	      self.connect()
	      n=self.cur.execute(sql)
	      return n
	   except MySQLdb.Error as e:
               print("seccond test, Mysql Error:%s\nSQL:%s" %(e,sql.encode("utf8")))
               return None

    def queryRow(self,sql):
        self.query(sql)
        result = self.cur.fetchone()
        return result

    def queryAll(self,sql):
        self.query(sql)
        result=self.cur.fetchall()
        desc =self.cur.description
        d = []
        for inv in result:
             _d = {}
             for i in range(0,len(inv)):
                 _d[desc[i][0]] = str(inv[i])
             d.append(_d)
        return d

    def query_con_map(self,p_table_name,p_con_map):
        p_data={}
        for key in p_con_map:
            if type(p_con_map[key])==type('str'):
                p_data[key]="'"+self.escape_string(str(p_con_map[key]))+"'"
            else:
                p_data[key]=self.escape_string(str(p_con_map[key]))
        con_str=' AND '.join([el+'='+str(p_data[el]) for el in p_data])
        real_sql="SELECT 1 FROM " +p_table_name+" WHERE "+con_str
	#print real_sql
        res=self.queryRow(real_sql)
        if type(res)==type((1,2)):
           return res[0] == 1
        return False
       
    def insert(self,p_table_name,p_input):
        p_data={}
        for key in p_input:
            if type(p_input[key])==type('str'):
                p_data[key]="'"+self.escape_string(str(p_input[key]))+"'"
            else:
                 p_data[key]=self.escape_string(str(p_input[key]))
        key   = ','.join(p_data.keys())
        value = ','.join(p_data.values())
        real_sql = "INSERT INTO " + p_table_name + " (" + key + ") VALUES (" + value + ")"
        self.query(real_sql)
        self.commit()
   
    def update(self,p_table_name,p_input,p_con_map):
        p_data={}
        p_con_data={}
        for key in p_input:
            if type(p_input[key])==type('str'):
                p_data[key]="'"+self.escape_string(str(p_input[key]))+"'"
            else:
                 p_data[key]=self.escape_string(str(p_input[key]))
        for key in p_con_map:
            if type(p_con_map[key])==type('str'):
                p_con_data[key]="'"+self.escape_string(str(p_con_map[key]))+"'"
            else:
                p_con_data[key]=self.escape_string(str(p_con_map[key]))
        con_str=' AND '.join([el+'='+str(p_con_data[el]) for el in p_con_data])
        update_str=' , '.join(el+'='+str(p_data[el]) for el in p_data)
        real_sql="UPDATE IGNORE "+p_table_name+" SET "+update_str+" WHERE "+con_str
        self.query(real_sql)
        self.commit()
        
    def escape_string(self,str):
        return self.conn.escape_string(str)

    def getLastInsertId(self):
        return self.cur.lastrowid

    def rowcount(self):
        return self.cur.rowcount

    def commit(self):
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()

if __name__=="__main__":
    oscDB = CMysql("10.129.135.179",3369,"haifeng","cao","osc_check","utf8")
    print oscDB.escape_string("''")
    sql = "select Falbum_id , Title from osc_check.osc_album limit 2"
    print oscDB.queryAll(sql)
