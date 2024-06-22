from dotenv import load_dotenv
import os
import mysql.connector


def connect_to_db():
    load_dotenv()

    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    database = os.getenv('DB_NAME')
    port = os.getenv('DB_PORT')

    # Connexion à la base de données
    cnx = mysql.connector.connect(user=user, password=password, host=host, database=database, port=port)
    cursor = cnx.cursor()
    return cnx, cursor


def get_parameters():
    cnx, cursor = connect_to_db()
    try:
        query = "SELECT * FROM parameters"
        cursor.execute(query)
        parameters = cursor.fetchall()
    except mysql.connector.Error:
        return False
    finally:
        cursor.close()
        cnx.close()
    return parameters

def modify_parameters(parameters):
    cnx, cursor = connect_to_db()
    try:
        for param in parameters:
            query = "UPDATE parameters SET value = %s WHERE name = %s"
            cursor.execute(query, (param[1], param[0]))
        cnx.commit()
        print("Parameters updated.")
    except mysql.connector.Error:
        return False
    finally:
        cursor.close()
        cnx.close()
    return True


def get_all_known_barks():
    cnx, cursor = connect_to_db()
    try:
        query = "SELECT * FROM knownbarks"
        cursor.execute(query)
        barks = cursor.fetchall()
    except mysql.connector.Error:
        return False
    finally:
        cursor.close()
        cnx.close()
    return barks


def get_number_of_known_barks():
    cnx, cursor = connect_to_db()
    try:
        query = "SELECT COUNT(distinct bark_id) FROM knownbarks"
        cursor.execute(query)
        number_of_known_barks = cursor.fetchone()[0]
    except mysql.connector.Error:
        return False
    finally:
        cursor.close()
        cnx.close()
    return number_of_known_barks


def get_known_barks():
    cnx, cursor = connect_to_db()
    try:
        barks = get_all_known_barks()
        known_barks = [[] for _ in range(get_number_of_known_barks())]
        for (_, bark_id, harmonic, amplitude) in barks:
            bark_info = (harmonic, amplitude)
            known_barks[bark_id - 1].append(bark_info)
    except mysql.connector.Error as e:
        print("Error", e)
        return False
    finally:
        cursor.close()
        cnx.close()
    return known_barks

def get_last_barks():
    cnx, cursor = connect_to_db()
    try:
        query = "SELECT date, mode, voice FROM Barks WHERE date >= CURRENT_TIMESTAMP - INTERVAL 3 DAY ORDER BY date DESC LIMIT 5"
        cursor.execute(query)
        last_barks = cursor.fetchall()
    except mysql.connector.Error as e:
        print("Erreur lors de la récupération des derniers aboiements", e)
        return False
    finally:
        cursor.close()
        cnx.close()
    return last_barks

def insert_bark(bark: list):
    cnx, cursor = connect_to_db()
    try:
        query = "INSERT INTO Barks (date, mode, voice) VALUES (%s, %s, %s)"
        cursor.execute(query, (bark[0], bark[1], bark[2]))
        cnx.commit()
    except mysql.connector.Error:
        return False
    finally:
        cursor.close()
        cnx.close()
    return True

#def insert_bark(harmonics: list[[int, float]]):
#    cnx, cursor = connect_to_db()
#    try:
#        max_id = get_max_bark_id(cursor)
#        for harmonic, amplitude in harmonics:
#            query = "INSERT INTO knownbarks (bark_id, harmonic, amplitude) VALUES (%s, %s, %s)"
#            cursor.execute(query, (max_id, harmonic, amplitude))
#        cnx.commit()
#    except mysql.connector.Error:
#        return False
#    finally:
#        cursor.close()
#        cnx.close()
#    return True
#
#
#def get_max_bark_id(cursor):
#    max_id_query = "SELECT MAX(bark_id) FROM knownbarks"
#    cursor.execute(max_id_query)
#    max_id = cursor.fetchone()
#    max_id_query = max_id[0] if max_id else 0
#    max_id = max_id_query + 1
#    return max_id
