#! /usr/bin/env python
# coding=utf-8
"""By gaopeng
"""
import boto3
import logging
import os
from optparse import OptionParser
import re
from re import search
import socket
import sys
import urllib.request

parser = OptionParser()
parser.add_option('-R', '--record', type='string', dest='record_to_update', help='The A record to update.')
parser.add_option('-U', '--url', type='string', dest='ip_get_url', help='URL that returns the current IP address.')
parser.add_option('-v', '--verbose', dest='verbose', default=False, help='Enable Verbose Output.', action='store_true')
(options, args) = parser.parse_args()

is_ipv6 = 0

if options.record_to_update is None:
    logging.error('Please specify an A record with the -R switch.')
    parser.print_help()
    sys.exit(-1)
if options.ip_get_url is None:
    logging.error('Please specify a URL that returns the current IP address with the -U switch.')
    parser.print_help()
    sys.exit(-1)
if options.verbose:
    logging.basicConfig(
        level=logging.INFO,
    )
record_to_update = options.record_to_update 
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
req = urllib.request.Request(options.ip_get_url, headers=hdr)
try:
    page = urllib.request.urlopen(req)
except urllib.request.HTTPError as e:
    logging.error("Could not retrieve content from url")

content = page.read()

ip_list = re.findall(r'[0-9]+(?:\.[0-9]+){3}', str(content))


if len(ip_list) < 1:
    print("This is not ipv4 address")
    ip_list = re.findall(r"(?<![:.\w])(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}(?![:.\w])", str(content), re.I)
    is_ipv6 = 1
    print(ip_list[0])
    if len(ip_list) < 1:    
        logging.error("Unable to find an IP address from within the URL:  %s" % options.ip_get_url)
        sys.exit(-1)

current_ip = ip_list[0] 
print("current_ip is {}".format(current_ip))

zone_to_update = os.getenv("ROUTE53_ZONE")
if zone_to_update == None:                                                                                            
    logging.error('Please specify the ID of the hosted zone.')
    sys.exit(-1)

if is_ipv6 == 1:                                                                                                  
    socket.inet_pton(socket.AF_INET6,current_ip)                                                                   
else:                                                                                                             
    socket.inet_pton(socket.AF_INET,current_ip)  

# Update the route53
if is_ipv6 == 1:
    type = 'AAAA'
else:
    type = 'A'

client = boto3.client('route53')

response = client.change_resource_record_sets(
    HostedZoneId=zone_to_update,
    ChangeBatch={
        'Comment': 'talaria',
        'Changes': [
            {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': record_to_update,
                    'Type': type,
                    'TTL': 60,
                    'ResourceRecords': [
                        {
                            'Value': current_ip
                        },
                    ],
                }
            },
        ]
    }
)
print(response)
print("End")

