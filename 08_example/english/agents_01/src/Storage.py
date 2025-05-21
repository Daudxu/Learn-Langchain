# storage.py
# 全局用户存储
user_storage = {}

# 可以添加一些辅助函数
def add_user(user_id, user_data):
    user_storage[user_id] = user_data

def get_user(user_id):
    return user_storage.get(user_id)

def get_all_users():
    return user_storage

def delete_user(user_id):
    if user_id in user_storage:
        del user_storage[user_id]
        return True
    return False
