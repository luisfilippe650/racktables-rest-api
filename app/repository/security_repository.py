def get_user(username , hashPassword, cursor):
    sql = "SELECT id FROM UserAccount WHERE user_name = %s and password_hash = %s LIMIT 1"
    cursor.execute(sql, (username, hashPassword))
    return cursor.fetchone()
