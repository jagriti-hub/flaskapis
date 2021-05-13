curl -X POST -H "Content-Type: application/json" -H "auth: XXXXX" -d '{"serviceid":"s12345","resourceid":"r123457","type":"PYTHON_FLASK","versionid":"v1","versionname":"v1test"}' "http://localhost:10001/live/v1/resource"

curl -X GET -H "Content-Type: application/json" -H "auth: XXXXXX" "http://localhost:10001/live/v1/resource/r123457"

curl -X GET -H "Content-Type: application/json" -H "auth: XXXXXX" "http://localhost:10001/live/v1/resource/s12345/v1/r123457/logs"

curl -X GET -H "Content-Type: application/json" -H "auth: XXXXXXX" "http://localhost:10001/live/v1/resource/s12345/v1/r123457/buildlog"

curl -X GET -H "Content-Type: application/json" -H "auth: XXXXXXX" "http://localhost:10001/live/v1/resource/s12345/v1/r123457/output"

curl -X POST -H "Content-Type: application/json" -H "auth: XXXXXXX" -d '{"serviceid":"s12345","resourceid":"r123457","type":"PYTHON_FLASK","versionid":"v1","versionname":"v1test"}' "http://localhost:10001/live/v1/resource/update"

curl -X DELETE -H "Content-Type: application/json" -H "auth: XXXXXXX"" "http://localhost:10001/live/v1/resource/s12345/v1/r123457"