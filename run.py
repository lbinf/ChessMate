from app import app
# 入口是哪个文件,就导入哪个文件(文件夹名.入口文件名)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)