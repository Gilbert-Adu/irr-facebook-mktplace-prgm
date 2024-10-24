#add tasks to dynamo db
#automate running tasks in the background

import boto3 # type: ignore
import uuid
from datetime import datetime




dynamodb = boto3.resource('dynamodb',
                          region_name='',
                          aws_access_key_id='',
                          aws_secret_access_key=''
                          )

tasksTable = dynamodb.Table('TasksTable')

{
    "query": "",
    "city": "",
    "minPrice": "",
    "maxPrice": "",
    "brand": "",
    "productLine": "",
    "network": "",
    "condition": "list",

}

def insert_task_to_db(user_id, url, query, city, minPrice, maxPrice, brand, productLine, network, condition):
    try:
        task_id = str(uuid.uuid4())


        tasksTable.put_item(
            Item={
                'UserId': user_id,
                'TaskId': task_id,
                'url': url,
                'query': query,
                'city': city,
                'maxPrice': maxPrice,
                'minPrice': minPrice,
                'brand': brand,
                'productLine': productLine,
                'network': network,
                'condition': condition,
                'createdAt': str(datetime.now())
            }
        )
        print("inserted new task")
        
        return 'success'
    
    except Exception as e:
        print(f"could not create task: ", e)
        return e
    
def get_tasks_by_id(user_id):
    try:

        response = tasksTable.scan(
        FilterExpression="UserId = :user_id",
        ExpressionAttributeValues={':user_id':user_id}
    )
        
        # Retrieve items from the response
        items = response.get('Items', [])
        return items  # Return the list of items
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


"""
use TaskId for partition
table name = TasksTable
condition
[ { "S" : "new" } ]
[ { "S" : "new" } ]
[ { "S" : "new" }, { "S" : "used_like_new" }, { "S" : "used_good" }, { "S" : "used_fair" } ]

"""