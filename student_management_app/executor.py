from datetime import datetime
from pathlib import Path
import subprocess
import os
import shutil


def write_to_file(file_path, code):
    is_file_created = False
    # Write to empty file
    if file_path:
        try:
            with open(file_path, 'w') as codefile:
                codefile.write(code)
            print("File write completed : ", file_path)
            is_file_created = True
        except Exception as e:
            print("File write failed : ", file_path, "\n\n", e)
    return is_file_created


def execute_code(code, stdin, language, class_name):
    timestamp = datetime.now().strftime("%m_%d_%Y__%H_%M_%S")

    print("---code---", code)
    print("---stdin---", stdin)
    print("---language---", language)
    print("---class_name---", class_name)

    relative_code_path = os.path.join(os.getcwd(),'media','code')
    full_source_coding_dir = os.path.join(relative_code_path,"source_code")
    full_output_dir = os.path.join(relative_code_path,"output")
    full_source_coding_path = os.path.join(full_source_coding_dir,language)
    full_output_path = os.path.join(full_output_dir,language)

    for path in [full_source_coding_path,full_output_path]:
        folder_path = Path(path)
        folder_path.mkdir(parents=True, exist_ok=True)

    file_name = ""
    output_file = ""
    if language in ['java','cs']:
        temp_folder = f"temp_{timestamp}"
        full_source_coding_path = os.path.join(full_source_coding_path,temp_folder)
        full_output_path = os.path.join(full_output_path,temp_folder)
        os.mkdir(full_source_coding_path)
        os.mkdir(full_output_path)
        class_name = class_name.strip()
        file_name = class_name + '.' + language
    else:
        file_name = f"temp_{timestamp}" + '.' + language
        if language == "node_js":
            file_name = file_name.replace(language,'js')
        if language == "r":
            file_name = file_name.replace(language,language.upper())

    print('full_coding_dir', full_source_coding_path)
    print('full_output_dir', full_output_path)

    output = "NO response returned!!"

    is_file_created = write_to_file(os.path.join(full_source_coding_path,file_name),code)
    if is_file_created:
        if language == 'py':
            command = f"cd {full_source_coding_path} && python {file_name}"
        elif language == 'py3':
            command = f"cd {full_source_coding_path} && python3 {file_name}"
        elif language == 'java':
            command = f"cd {full_source_coding_path} && javac {file_name} && java {file_name.replace('.java','')}"
        elif language == 'cpp':
            output_file = os.path.join(full_output_path, file_name.replace('.cpp','.exe'))
            command = f"g++ {full_source_coding_path}/{file_name} -o {output_file} && {output_file}"
        elif language == 'c':
            output_file = os.path.join(full_output_path, file_name.replace('.c','.exe'))
            command = f"gcc {full_source_coding_path}/{file_name} -o {output_file} && {output_file}"
        elif language == 'c#':
            output_file = os.path.join(full_output_path, file_name.replace('.cs','.exe'))
            command = f"mcs -out:{output_file} {full_source_coding_path}/{file_name}"
        elif language == 'r':
            command = f"Rscript {full_source_coding_path}/{file_name}"
        elif language == 'rb':
            command = f"ruby {full_source_coding_path}/{file_name}"
        elif language == 'go':
            command = f"go run {full_source_coding_path}/{file_name}"        
        elif language == 'pl':
            command = f"perl {full_source_coding_path}/{file_name}"
        elif language == 'vb':
            output_file = os.path.join(full_output_path, file_name.replace(language,'.exe'))
            command = f"vbnc -out:{output_file} {full_source_coding_path}/{file_name} && mono {output_file}"        
        elif language == 'node_js':
            command = f"node {full_source_coding_path}/{file_name.replace(language,'js')}"
        elif language == 'js':
            pass

        if language == 'js':
            output= "No result!!"
        else:
            try:
                print("command : ", command)
                p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, stdin=subprocess.PIPE,stderr=subprocess.STDOUT)
                p.stdin.write(str.encode(stdin))
                (output, err) = p.communicate()
                p.stdin.close()
                output = output.decode("utf-8")
                output = output.replace(full_source_coding_path, '')
            except subprocess.CalledProcessError as exc:
                print("Status : FAIL", exc.returncode, exc.output)
                output = exc.output
            else:
                # if temp folder then delete entire temp folder and it's content else
                # delete only the temp_timestamp.extension files from
                # both source code and output dir
                if "temp" in full_source_coding_path:
                    shutil.rmtree(full_source_coding_path)
                    shutil.rmtree(full_output_path)
                else:
                    os.remove(os.path.join(full_source_coding_path,file_name))
                    if output_file and os.path.exists(os.path.join(full_source_coding_path,output_file)):
                        os.remove(os.path.join(full_source_coding_path,output_file))
    else:
        output = "ERROR: File Not Created!!!"
    return output
