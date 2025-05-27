import os
import zipfile
import shutil

# 原始文件名：例如PA01-0018-com.nra.flyermaker-90.xapk
# 希望从中解压并提取出主apk：com.nra.flyermaker.apk
# 并将com.nra.flyermaker.apk命名为PA01-0018-com.nra.flyermaker-90.apk


# 获取当前目录下所有.xapk文件
xapk_files = [file for file in os.listdir('.') if file.endswith('.xapk')]

# 循环处理每个文件
for file in xapk_files:
    print(file)
    # PA01-0018-com.nra.flyermaker-90.xapk

    # 解压缩到当前目录下的与文件同名的文件夹中
    with zipfile.ZipFile(file, 'r') as zip_ref:
        folder_name = os.path.splitext(file)[0]
        zip_ref.extractall(folder_name)

    # 在解压缩后的文件夹中找到apk文件并进行重命名
    folder_files = os.listdir(folder_name)
    apk_files = [name for name in folder_files if name.endswith('.apk')]
    for apk_file in apk_files:

        # 找到解压后的主apk
        if os.path.splitext(apk_file)[0] in os.path.splitext(file)[0]:
            print(apk_file)  
            # com.nra.flyermaker.apk

            apk_path = os.path.join(folder_name, apk_file)
            print("old apk name : " + apk_path) 
            # old apk name : PA01-0018-com.nra.flyermaker-90/com.nra.flyermaker.apk

            new_apk_path = os.path.join(folder_name, folder_name+'.apk')
            print("new apk name : " + new_apk_path) 
            # new apk name : PA01-0018-com.nra.flyermaker-90/PA01-0018-com.nra.flyermaker-90.apk

            os.rename(apk_path, new_apk_path)

            # 将./PA01-0018-com.nra.flyermaker-90/PA01-0018-com.nra.flyermaker-90.apk 移动至 ./PA01-0018-com.nra.flyermaker-90.apk
            shutil.move(new_apk_path, "./"+folder_name+'.apk')

            # 删除./PA01-0018-com.nra.flyermaker-90/文件夹
            shutil.rmtree(folder_name)
