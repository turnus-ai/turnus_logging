"""
Example of using turnus_logging in AWS Lambda functions.

For Sentry integration in Lambda:
1. Add sentry-sdk to requirements.txt or Lambda layer
2. Set environment variables in Lambda configuration:
   - SENTRY_DSN=https://your-dsn@sentry.io/project
   - SENTRY_ENVIRONMENT=production (optional)
   - LOG_LEVEL=INFO (optional)
3. Deploy with dependencies bundled or in a layer

Note: Lambda has limited execution time, but Sentry SDK is async and non-blocking.
Logs and errors will be sent to Sentry before Lambda terminates.
"""

from turnus_logging import setup_logging, get_logger, log_context
import json
import os

# Setup logging once (outside handler for container reuse)
# Sentry is automatically initialized from environment variables:
# - SENTRY_DSN (required for Sentry)
# - SENTRY_ENVIRONMENT (optional, defaults to config or 'production')
setup_logging(service_name='my-lambda-function')

# Or use explicit config:
# setup_logging(
#     service_name='my-lambda-function',
#     sentry={
#         'dsn': os.environ.get('SENTRY_DSN'),
#         'environment': os.environ.get('SENTRY_ENVIRONMENT', 'production'),
#         'event_level': 'ERROR',      # Send ERROR+ to Sentry as events
#         'breadcrumb_level': 'INFO',  # Collect INFO+ as breadcrumbs
#     }
# )

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    Lambda handler with automatic context injection.
    
    Args:
        event: Lambda event (API Gateway, SQS, EventBridge, etc.)
        context: Lambda context object
    """
    
    # Extract context from Lambda
    lambda_context = {
        'request_id': context.request_id,  # Lambda's built-in request ID
        'function_name': context.function_name,
        'function_version': context.function_version,
        'memory_limit': context.memory_limit_in_mb,
    }
    
    # For API Gateway events, add HTTP context
    if 'requestContext' in event:
        lambda_context.update({
            'http_method': event.get('httpMethod'),
            'path': event.get('path'),
            'source_ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp'),
        })
        
        # Extract custom headers if needed
        headers = event.get('headers', {})
        if 'x-api-version' in headers:
            lambda_context['api_version'] = headers['x-api-version']
    
    # For SQS events
    if 'Records' in event and event['Records']:
        record = event['Records'][0]
        if record.get('eventSource') == 'aws:sqs':
            lambda_context['message_id'] = record.get('messageId')
            lambda_context['queue_name'] = record.get('eventSourceARN', '').split(':')[-1]
    
    # Use log_context for the entire Lambda invocation
    with log_context(**lambda_context):
        try:
            logger.info("Lambda function started")
            
            # Your business logic here
            result = process_event(event)
            
            logger.info("Lambda function completed successfully")
            
            # For API Gateway, return proper response
            if 'requestContext' in event:
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Request-ID': context.request_id,  # Echo request ID
                    },
                    'body': json.dumps(result)
                }
            
            return result
            
        except Exception as e:
            logger.exception("Lambda function failed")
            
            if 'requestContext' in event:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Request-ID': context.request_id,
                    },
                    'body': json.dumps({'error': str(e)})
                }
            
            raise


def process_event(event):
    """Process the Lambda event."""
    logger.info(f"Processing event: {event.get('httpMethod', 'N/A')} {event.get('path', 'N/A')}")
    
    # Add more context during processing if needed
    from turnus_logging import append_context
    
    # Example: if you extract user info from the event
    if 'requestContext' in event:
        authorizer = event.get('requestContext', {}).get('authorizer', {})
        if 'userId' in authorizer:
            append_context({'user_id': authorizer['userId']})
    
    # Your business logic
    return {
        'message': 'Hello from Lambda',
        'status': 'success'
    }


# For Lambda with Application Load Balancer
def alb_lambda_handler(event, context):
    """Handler for Lambda behind Application Load Balancer."""
    
    lambda_context = {
        'request_id': context.request_id,
        'function_name': context.function_name,
    }
    
    # ALB-specific context
    if 'requestContext' in event and 'elb' in event['requestContext']:
        lambda_context['target_group_arn'] = event['requestContext']['elb'].get('targetGroupArn')
    
    headers = event.get('headers', {})
    lambda_context['http_method'] = event.get('httpMethod')
    lambda_context['path'] = event.get('path')
    
    with log_context(**lambda_context):
        logger.info("ALB Lambda invoked")
        
        # Process request
        result = {'status': 'ok'}
        
        return {
            'statusCode': 200,
            'statusDescription': '200 OK',
            'headers': {
                'Content-Type': 'application/json',
                'X-Request-ID': context.request_id,
            },
            'body': json.dumps(result)
        }


# For EventBridge/CloudWatch Events
def eventbridge_lambda_handler(event, context):
    """Handler for EventBridge scheduled or custom events."""
    
    lambda_context = {
        'request_id': context.request_id,
        'function_name': context.function_name,
        'event_source': event.get('source'),
        'event_type': event.get('detail-type'),
    }
    
    with log_context(**lambda_context):
        logger.info("EventBridge event received")
        
        detail = event.get('detail', {})
        logger.info(f"Processing event detail: {detail}")
        
        # Process event
        return {'status': 'processed'}


# For SQS queue processing
def sqs_lambda_handler(event, context):
    """Handler for Lambda triggered by SQS."""
    
    base_context = {
        'request_id': context.request_id,
        'function_name': context.function_name,
    }
    
    with log_context(**base_context):
        logger.info(f"Processing {len(event['Records'])} SQS messages")
        
        results = []
        for record in event['Records']:
            # Create context for each message
            msg_context = {
                'message_id': record['messageId'],
                'queue_name': record['eventSourceARN'].split(':')[-1],
            }
            
            with log_context(**msg_context):
                try:
                    logger.info("Processing SQS message")
                    body = json.loads(record['body'])
                    
                    # Process message
                    result = process_sqs_message(body)
                    results.append(result)
                    
                    logger.info("Message processed successfully")
                    
                except Exception as e:
                    logger.exception("Failed to process SQS message")
                    # Could implement partial batch failure here
        
        return {'processed': len(results)}


def process_sqs_message(body):
    """Process individual SQS message."""
    logger.info(f"Message body: {body}")
    return {'status': 'ok'}


# For S3 events
def s3_lambda_handler(event, context):
    """Handler for Lambda triggered by S3 events."""
    
    base_context = {
        'request_id': context.request_id,
        'function_name': context.function_name,
    }
    
    with log_context(**base_context):
        logger.info(f"Processing {len(event['Records'])} S3 events")
        
        for record in event['Records']:
            # Context for each S3 event
            s3_context = {
                'event_name': record['eventName'],  # e.g., 'ObjectCreated:Put'
                'bucket': record['s3']['bucket']['name'],
                'object_key': record['s3']['object']['key'],
                'object_size': record['s3']['object'].get('size'),
            }
            
            with log_context(**s3_context):
                logger.info("Processing S3 object")
                
                # Your S3 processing logic
                process_s3_object(
                    bucket=s3_context['bucket'],
                    key=s3_context['object_key']
                )
                
                logger.info("S3 object processed successfully")


def process_s3_object(bucket, key):
    """Process S3 object."""
    logger.info(f"Processing s3://{bucket}/{key}")
    # Your logic here
    

# For DynamoDB Streams
def dynamodb_lambda_handler(event, context):
    """Handler for Lambda triggered by DynamoDB Streams."""
    
    base_context = {
        'request_id': context.request_id,
        'function_name': context.function_name,
    }
    
    with log_context(**base_context):
        logger.info(f"Processing {len(event['Records'])} DynamoDB stream records")
        
        for record in event['Records']:
            # Context for each DynamoDB record
            ddb_context = {
                'event_name': record['eventName'],  # INSERT, MODIFY, REMOVE
                'table_name': record['eventSourceARN'].split('/')[-3],
                'sequence_number': record['dynamodb'].get('SequenceNumber'),
            }
            
            # Extract primary key if available
            if 'Keys' in record['dynamodb']:
                keys = record['dynamodb']['Keys']
                if 'id' in keys:
                    ddb_context['record_id'] = keys['id'].get('S') or keys['id'].get('N')
            
            with log_context(**ddb_context):
                logger.info("Processing DynamoDB stream record")
                
                # Process the change
                new_image = record['dynamodb'].get('NewImage')
                old_image = record['dynamodb'].get('OldImage')
                
                process_dynamodb_change(
                    event_name=ddb_context['event_name'],
                    new_image=new_image,
                    old_image=old_image
                )
                
                logger.info("DynamoDB record processed")


def process_dynamodb_change(event_name, new_image, old_image):
    """Process DynamoDB stream change."""
    logger.info(f"Change type: {event_name}")
    # Your logic here


# For SNS notifications
def sns_lambda_handler(event, context):
    """Handler for Lambda triggered by SNS."""
    
    base_context = {
        'request_id': context.request_id,
        'function_name': context.function_name,
    }
    
    with log_context(**base_context):
        logger.info(f"Processing {len(event['Records'])} SNS notifications")
        
        for record in event['Records']:
            sns = record['Sns']
            
            sns_context = {
                'message_id': sns['MessageId'],
                'topic_arn': sns['TopicArn'],
                'subject': sns.get('Subject', 'N/A'),
                'timestamp': sns['Timestamp'],
            }
            
            with log_context(**sns_context):
                logger.info("Processing SNS notification")
                
                message = json.loads(sns['Message']) if sns['Message'].startswith('{') else sns['Message']
                process_sns_message(message)
                
                logger.info("SNS notification processed")


def process_sns_message(message):
    """Process SNS message."""
    logger.info(f"Message: {message}")
    # Your logic here


# For Kinesis streams
def kinesis_lambda_handler(event, context):
    """Handler for Lambda triggered by Kinesis Data Streams."""
    
    base_context = {
        'request_id': context.request_id,
        'function_name': context.function_name,
    }
    
    with log_context(**base_context):
        logger.info(f"Processing {len(event['Records'])} Kinesis records")
        
        for record in event['Records']:
            kinesis_context = {
                'sequence_number': record['kinesis']['sequenceNumber'],
                'partition_key': record['kinesis']['partitionKey'],
                'stream_arn': record['eventSourceARN'],
                'shard_id': record['eventID'].split(':')[0],
            }
            
            with log_context(**kinesis_context):
                logger.info("Processing Kinesis record")
                
                # Decode the data
                import base64
                data = base64.b64decode(record['kinesis']['data'])
                decoded_data = json.loads(data)
                
                process_kinesis_record(decoded_data)
                
                logger.info("Kinesis record processed")


def process_kinesis_record(data):
    """Process Kinesis record."""
    logger.info(f"Record data: {data}")
    # Your logic here


# For Step Functions
def step_function_lambda_handler(event, context):
    """Handler for Lambda invoked by AWS Step Functions."""
    
    lambda_context = {
        'request_id': context.request_id,
        'function_name': context.function_name,
        'execution_id': event.get('executionId', 'N/A'),
        'state_name': event.get('stateName', 'N/A'),
    }
    
    with log_context(**lambda_context):
        logger.info("Step Function task started")
        
        # Extract input from Step Function
        input_data = event.get('input', {})
        
        # Add more context from input if available
        if 'userId' in input_data:
            from turnus_logging import append_context
            append_context({'user_id': input_data['userId']})
        
        # Process the task
        result = process_step_function_task(input_data)
        
        logger.info("Step Function task completed")
        
        return result


def process_step_function_task(input_data):
    """Process Step Function task."""
    logger.info(f"Processing task with input: {input_data}")
    # Your logic here
    return {'status': 'completed', 'result': 'success'}
