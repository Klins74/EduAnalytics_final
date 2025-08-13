import psycopg2

if __name__ == "__main__":
    try:
        conn = psycopg2.connect(
            dbname="eduanalytics",
            user="canvas_user",
            password="password",
            host="localhost",
            port=5432
        )
        print("Connection successful!")
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    try:
        conn = psycopg2.connect(
            dbname="eduanalytics",
            user="edua",
            password="test",
            host="localhost",
            port=5432
        )
        print("Connection successful!")
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")