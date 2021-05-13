FROM docker:19
RUN apk add python3 py3-pip
RUN mkdir buildfolder
WORKDIR buildfolder
ADD requirement.txt ./requirement.txt
RUN pip3 install -r ./requirement.txt
ADD app.py ./app.py
ADD ecrdocker.py ./ecrdocker.py
ADD generatebuildcode.py ./generatebuildcode.py
ADD s3files.py ./s3files.py
ADD resourcedeployment.py ./resourcedeployment.py
ADD getdeploymentstatus.py ./getdeploymentstatus.py