## Transfer protocol

When the client need to send informations to the server.\
The request will have the following information :
- the action
- the url
- the request id, which need to be new for each request
- the connexion token, it is used to identify account between servers
- optional - the data type, if the request include data
- optional - the data lenght, if the request include data
- optional - the data
> Action Url Id Token [DataType [DataLenght\
> [Data

When the client send data, the server have to respond.\
The response will have the following information :
- the code, which follow the http status code
- the response id, which is the same as the request id sent by
the client
- the data type
- the data lenght
- the data
> Code Id DataType DataLenght\
> Data

The server can also send spontaneous information, in this case
the response id will be equal to a dot.

### Parameters description

- Action\
The action is here to help the server to know what to do, if the
client ask to log, ask for information or post something.\
There will be 3 possible action : LOG, GET, POST

- URL\
The URL is here to give more information about the action, it has
the same shape than HTTP URLs.\
e.g. /path/to/use\
note: the url can't get any arguments or use the interrogation mark.
- ID\
The id exists to link requests and responses, it helps the client
to know which response is for which request.\
The id is a numeric value of lenght 8.
- Token\
The account token is here to identify the client connection,
because there can be multiple servers which will work with
the same account.\
The token is an alphanumeric value of lenght 16.
- Code\
The code is the response from the server, either something went bad or
the response is usable.
- Data type\
The data type is here to know which kind of data we have, it can get\
three value : TEXT, JSON, IMAGE
- Data lenght\
This is the number of bytes the data is composed of.
- Data\
The data linked whit the header, it is utf-8 if this is a TEXT or
JSON data, or bytes for IMAGE.
