curl -X GET -H "userid: jagriti.s@archeplay.com" http://localhost:8000/design/v1/product
curl -X POST -H "content-type: application/json" -H "userid: jagriti.s@archeplay.com" http://localhost:8000/design/v1/product -d '{"productname":"testprod"}'
curl -X GET http://localhost:8000/design/v1/product/prodb6c108c4
curl -X DELETE http://localhost:8000/design/v1/product/prodb6c108c4
curl -X GET  http://localhost:8000/design/v1/service/prod4d906991
curl -X POST -H "content-type: application/json" -H "userid: jagriti.s@archeplay.com" http://localhost:8000/design/v1/service/prod4d906991 -d '{"servicename":"testservice","servicetype":"dynamodb_python_eks","description":"testing service"}'
curl -X GET  http://localhost:8000/design/v1/service/prod4d906991/serviceb07d667b
curl -X DELETE  http://localhost:8000/design/v1/service/prod4d906991/serviceb07d667b
curl -X GET http://localhost:8000/design/v1/api/prod003e66d6/service54263fea/apifc63b43b
curl -X POST -H "content-type: application/json" http://localhost:8000/design/v1/api/prod003e66d6/service54263fea/apifc63b43b/version -d '{"versionname":"testver"}'
curl -X DELETE http://localhost:8000/design/v1/api/prod003e66d6/service54263fea/apifc63b43b/v-71dc061b
curl -X POST -H "content-type: application/json" http://localhost:8000/design/v1/api/prod003e66d6/service54263fea/apifc63b43b/v-6467b057/resource -d '{"resourcename":"newres"}'
curl http://localhost:8000/design/v1/api/prod003e66d6/service54263fea/apifc63b43b/v-6467b057/resource
curl http://localhost:8000/design/v1/api/prod003e66d6/service54263fea/apifc63b43b/v-6467b057/resf4302d67
curl -X DELETE http://localhost:8000/design/v1/api/prod003e66d6/service54263fea/apifc63b43b/v-6467b057/res04d8d606
curl http://localhost:8000/design/v1/api/prod003e66d6/service54263fea/apifc63b43b/v-6467b057/resf4302d67/method
curl -X POST -H "content-type: application/json" http://localhost:8000/design/v1/api/prod003e66d6/service54263fea/apifc63b43b/v-6467b057/resf4302d67/method -d '{"methodtype":"GET","path":"/test"}'
curl http://localhost:8000/design/v1/api/prod003e66d6/service54263fea/apifc63b43b/v-6467b057/resf4302d67/methb6dedba0
curl -X DELETE http://localhost:8000/design/v1/api/prod003e66d6/service54263fea/apifc63b43b/v-6467b057/resf4302d67/meth8cc73637
curl -X PATCH -H "content-type: application/json" http://localhost:8000/design/v1/api/prod003e66d6/service54263fea/apifc63b43b/v-6467b057/resf4302d67/methb6dedba0 -d '{"requirements": "json\nboto3","import_code": "import json,boto3","function_code": "\ndynamodb = boto3.resource('dynamodb')\ntable=dynamodb.Table('asada')\n","main_code": "kwargs={\n    Key={'saas':input['saas']}\n}\ndata=table.get_item(**kwargs)['Item']\n"}'
curl http://localhost:8000/design/v1/data/service54263fea/v-6467b057/resf4302d67/database
curl -X POST -H "content-type: application/json" http://localhost:8000/design/v1/data/service54263fea/v-6467b057/resf4302d67 -d '{"description":"testdata"}'
curl http://localhost:8000/design/v1/data/service54263fea/v-6467b057/resf4302d67/database/db370e6ce6
curl -X DELETE http://localhost:8000/design/v1/data/service54263fea/v-6467b057/resf4302d67/database/db370e6ce6
curl -X POST -H "content-type: application/json" http://localhost:8000/design/v1/table/service54263fea/dbe5300686 -d '{"tablename":"newtable"}'
curl http://localhost:8000/design/v1/table/service54263fea/dbe5300686
curl http://localhost:8000/design/v1/table/service54263fea/dbe5300686/tbb172c64e
curl -X DELETE http://localhost:8000/design/v1/table/service54263fea/dbe5300686/tbb172c64e


curl -X POST -H "content-type: application/json" http://127.0.0.1:5000/datastore/v1/git/credentials -d '{"gitrepourl":"","gitusername":"","gitpassword":"","Region":"us-east-1"}'
curl -X POST -H "content-type: application/json" http://127.0.0.1:5000/datastore/v1/git/branches -d '{"gitrepourl":"https://git-codecommit.us-east-1.amazonaws.com/v1/repos/coderepotest"}'
curl -X POST -H "content-type: application/json" http://127.0.0.1:5000/datastore/v1/git/designpush -d '{"gitrepourl":"https://git-codecommit.us-east-1.amazonaws.com/v1/repos/coderepotest","commitmessage":"design commit","tagname":"d1"}'
curl -X POST -H "content-type: application/json" http://127.0.0.1:5000/datastore/v1/git/publish/s12345 -d '{"gitrepourl":"https://git-codecommit.us-east-1.amazonaws.com/v1/repos/coderepotest","commitmessage":"design commit","tagname":"d1"}'

curl http://localhost:8000/datastore/v1/git
curl -X POST -H "content-type: application/json" http://localhost:8000/datastore/v1/git/validate -d '{"gitrepourl":"testgitrepo","gitusername":"","gitpassword":"","connectiontype":"https"}'
curl -X POST -H "content-type: application/json" http://localhost:8000/datastore/v1/git/credentials -d '{"connectiontype":"https","gitrepourl":"https://git-codecommit.us-east-1.amazonaws.com/v1/repos/testgitrepo","gitusername":"","gitpassword":"=","Region":"us-east-1","branches":["design","publish"]}'
curl -X POST -H "content-type: application/json" http://localhost:8000/datastore/v1/git/branches -d '{"gitrepourl":"https://git-codecommit.us-east-1.amazonaws.com/v1/repos/gitdatastore"}'
curl -X POST -H "content-type: application/json" http://localhost:8000/datastore/v1/git/designpush -d '{"commitmessage":"design commit","tagname":"d1"}'
curl -X POST -H "content-type: application/json" http://localhost:8000/datastore/v1/git/publish/s12345/testoption -d '{"gitrepourl":"https://git-codecommit.us-east-1.amazonaws.com/v1/repos/gittestrepo","commitmessage":"design commit","tagname":"d1"}'
curl http://localhost:8000/datastore/v1/git/getbranches
curl -X POST -H "content-type: application/json" http://localhost:8000/datastore/v1/git/templatepull -d '{"connectiontype": "https", "templategiturl": "", "templategitpassword":"NrQ+", "templategitusername": "", "templategitbranch": "master"}'
curl -X POST -H "content-type: application/json" http://localhost:8000/datastore/v1/git/templatepull -d '{"connectiontype": "https", "templategiturl": "https://github.com/aravindarcheplay/test.git", "templategitpasswohttps://git-codecommit.us-east-1.amazonaws.com/v1/repos/ap-template-storerd":"sATYA@123", "templategitusername": "aravindarcheplay", "templategitbranch": "main"}'
