# Run this file only once during entire application life cycle
import logging
from walrus import Database


log = logging.getLogger("redis")

db = Database(port=6379)

# Create a stream to work with
stream_keys = ['face_recog']
# Write some sample data in the stream
for stream in stream_keys:
    db.xadd(stream, {'data': ''})
# Link a consumer group for the stream
cg = db.consumer_group('face_recog-cg', stream_keys)
cg.create()  # Create the consumer group.
cg.set_id('$')  # Change the id to the most recent one

resp = cg.read()  # Read all the sample data from stream.
