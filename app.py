# import os
# import sys
# import logging
# import serial
# import serial.tools.list_ports
# from flask import Flask, jsonify, request, render_template_string
# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)

# HTML_TEMPLATE = """
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Serial Communication Interface</title>
#     <style>
#         body { 
#             font-family: Arial, sans-serif; 
#             margin: 0; 
#             padding: 0; 
#             display: flex; 
#             justify-content: center; 
#             align-items: center; 
#             height: 100vh; 
#             background-color: #f7f7f7;
#         }
#         .container {
#             text-align: center;
#             padding: 20px;
#             background-color: white;
#             box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
#             border-radius: 8px;
#         }
#         h1 { 
#             color: #333; 
#         }
#         input, button { 
#             margin: 10px 0; 
#             padding: 5px; 
#             width: 100%;
#             max-width: 300px;
#         }
#         #result { 
#             margin-top: 20px; 
#             padding: 10px; 
#             background-color: #f0f0f0; 
#             width: 100%;
#             max-width: 300px;
#             word-wrap: break-word;
#         }
#     </style>
# </head>
# <body>
#     <div class="container">
#         <h1>Serial Communication Interface</h1>
#         <input type="number" id="baudRate" value="115200" placeholder="Baud Rate">
#         <input type="number" id="brightness" min="0" max="255" placeholder="Brightness (0-255)">
#         <button onclick="setBrightness()">Set Brightness</button>
#         <div id="result"></div>
#     </div>

#     <script>
#         function setBrightness() {
#             const comPort = 'COM4';  // Default COM port
#             const baudRate = document.getElementById('baudRate').value;
#             const brightness = document.getElementById('brightness').value;

#             fetch('/set_brightness', {
#                 method: 'POST',
#                 headers: {
#                     'Content-Type': 'application/json',
#                 },
#                 body: JSON.stringify({ com_port: comPort, baud_rate: baudRate, brightness: brightness }),
#             })
#             .then(response => response.json())
#             .then(data => {
#                 document.getElementById('result').textContent = JSON.stringify(data, null, 2);
#             })
#             .catch(error => console.error('Error:', error));
#         }
#     </script>
# </body>
# </html>


# """

# @app.route('/')
# def home():
#     return render_template_string(HTML_TEMPLATE)

# @app.route('/get_com_ports', methods=['GET'])
# def get_com_ports():
#     try:
#         ports = serial.tools.list_ports.comports()
#         com_ports = [port.device for port in ports]
#         return jsonify({"status": "success", "com_ports": com_ports}), 200
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500

# def handle_serial_communication(com_port, baud_rate, address, value=None):
#     try:
#         ser = serial.Serial(com_port, baud_rate, timeout=5)
        
#         if not ser.is_open:
#             return jsonify({"status": "error", "message": "Failed to open serial port"}), 500

#         cmd_gen = CMD(ser, dev_name='Athena640', idd='new')
        
#         if value is not None:
#             command_sent = [0xe0, 0x0, 0x1, 0x3e, 0xff, 0x3, 0x52, 0x50, address, int(value), 0xff, 0xfe]
#             cmd_gen.fpga_write(address, int(value))
#             response = cmd_gen.fpga_read(address)
#         else:
#             command_sent = [0xe0, 0x0, 0x1, 0x3e, 0xff, 0x3, 0x52, 0x50, address]
#             response = cmd_gen.fpga_read(address)

#         ser.close()
#         return format_response(response, command_sent)
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500

# def format_response(response, command_sent):
#     response_list = [
#         response['header'], response['packet_sequence'] >> 8, response['packet_sequence'] & 0xFF,
#         response['device_id'], response['device_number'], response['length'],
#         response['cmd_type'], response['cmd_status'], response['cmd'] >> 8, response['cmd'] & 0xFF,
#         response['data'][0], response['data'][1], response['data'][2], response['data'][3],
#         response['chksum'], response['footer1'], response['footer2']
#     ]
#     command_response = [hex(x) for x in response_list if isinstance(x, int)]
    
#     if response['cmd_status'] != 0x00:
#         return jsonify({"status": "error", "message": "Communication Failed"}), 500
    
#     result = (
#         (response['data'][0] << 24) |
#         (response['data'][1] << 16) |
#         (response['data'][2] << 8) |
#         response['data'][3]
#     )

#     return jsonify({
#         "status": "success",
#         "value": result,
#         "command_sent": ','.join([f'0x{cmd:02x}' for cmd in command_sent]),
#         "command_response": ','.join(command_response),
#         "register": hex(command_sent[8])
#     }), 200

# @app.route('/set_brightness', methods=['POST'])
# def set_brightness():
#     data = request.json
#     com_port = data.get('com_port')
#     baud_rate = int(data.get('baud_rate'))
#     brightness = data.get('brightness')
#     return handle_serial_communication(com_port, baud_rate, 0xd0, brightness)

# logger_d = logging.getLogger(__name__)

# cmd_log_file = "./cmd_log.txt"

# class CMD:
#     def __init__(self, ser=None, dev_name=None, idd='old'):
#         self.ser = ser
#         self.idd = idd
#         self.sequence = 0
#         self.mem_cmd_id = 0
#         self.mem_cmd_type = 0
#         self.dev_name = dev_name
#         self.logger = logger_d
#         logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
#         consoleHandler = logging.StreamHandler(sys.stdout)
#         consoleHandler.setFormatter(logFormatter)
#         consoleHandler.setLevel(logging.DEBUG)
#         self.logger.addHandler(consoleHandler)
        
#         if(self.idd=='new'):
#             self.init_cmd_new_idd()
#         else:
#             self.init_cmd_old_idd()
    
#     def __del__(self):
#         handlers = self.logger.handlers[:]
#         for handler in handlers:
#             handler.close()
#             self.logger.removeHandler(handler)
#             del handler
#         logging.shutdown()
        
#     def init_cmd_old_idd(self):
#         self.PING_CMD = 0xB0B0
#         self.FPGA_RD_REGS = 0x4000
#         self.FPGA_WR_REGS = 0x5000
#         self.SET_SDRAM_ADDR = 0x6000
#         self.SET_SDRAM_DATA = 0x6004
#         self.GET_SDRAM_DATA = 0x6008
#         self.SET_I2C = 0x7004
#         self.GET_I2C = 0x7008
#         self.SET_SENSOR_I2C = 0x7104
#         self.GET_SENSOR_I2C = 0x7108
#         self.SET_SPI = 0x3004
#         self.GET_SPI = 0x3008
#         self.SET_SD_ADDR = 0x2000
#         self.SET_SD_DATA = 0x2004
#         self.GET_SD_DATA = 0x2008
#         self.ERASE_QSPI_64KB = 0xA000
#         self.ERASE_QSPI_32KB = 0xA001
#         self.ERASE_QSPI_4KB  = 0xA002
#         self.ERASE_SAVE_QSPI = 0xA004
#         self.SNAPSHOT = 0xA00E
#         self.TRANS_SDRAM_TO_QSPI = 0xA003
#         self.TRANS_QSPI_TO_SDRAM = 0xE000
#         self.QSPI_STATUS_CMD     = 0xA008
#         self.TRANS_TEMP_TO_QSPI = 0xE00C
#         self.TEMP_RANGE0_SENSOR_INIT_WR_QSPI = 0xE00D
#         self.TEMP_RANGE1_SENSOR_INIT_WR_QSPI = 0xE00E
#         self.TEMP_RANGE2_SENSOR_INIT_WR_QSPI = 0xE00F
#         self.TEMP_RANGE3_SENSOR_INIT_WR_QSPI = 0xE010
        
#         self.BLK_SIZE= 512
#         self.header = 0xFE
#         self.dev_id = 0x3E
#         self.dev_no =  0xFF
        
#     def init_cmd_new_idd(self):
#         self.PING_CMD = 0xB0B0
#         self.FPGA_RD_REGS = 0x5000
#         self.FPGA_WR_REGS = 0x5000
#         self.SET_SDRAM_ADDR = 0x6000
#         self.SET_SDRAM_DATA = 0x6004
#         self.GET_SDRAM_DATA = 0x6004
#         self.SET_I2C = 0x7004
#         self.GET_I2C = 0x7004
#         self.SET_I2C_16B = 0x7005
#         self.GET_I2C_16B = 0x7005
#         self.SET_SENSOR_I2C = 0x7104
#         self.GET_SENSOR_I2C = 0x7104
#         self.SET_SPI = 0x3004
#         self.GET_SPI = 0x3004
#         self.SET_SD_ADDR = 0x2000
#         self.SET_SD_DATA = 0x2004
#         self.GET_SD_DATA = 0x2004
#         self.ERASE_SAVE_TABLE = 0xA004
#         self.ERASE_QSPI_64KB = 0xA000
#         self.ERASE_QSPI_32KB = 0xA001
#         self.ERASE_QSPI_4KB  = 0xA002
#         self.ERASE_SAVE_QSPI = 0xA004
#         self.SNAPSHOT = 0xA00E
#         self.TRANS_SDRAM_TO_QSPI = 0xA003
#         self.TRANS_QSPI_TO_SDRAM = 0xE000
#         self.QSPI_STATUS_CMD     = 0xA008
#         self.TRANS_TEMP_TO_QSPI  = 0xE00C
#         self.SAVE_USER_SETTINGS  = 0xA005
#         self.TEMP_RANGE0_SENSOR_INIT_WR_QSPI = 0xE00D
#         self.TEMP_RANGE1_SENSOR_INIT_WR_QSPI = 0xE00E
#         self.TEMP_RANGE2_SENSOR_INIT_WR_QSPI = 0xE00F
#         self.TEMP_RANGE3_SENSOR_INIT_WR_QSPI = 0xE010
#         self.TEMP_RANGE4_SENSOR_INIT_WR_QSPI = 0xE011
#         self.TEMP_RANGE5_SENSOR_INIT_WR_QSPI = 0xE012
#         self.TEMP_RANGE6_SENSOR_INIT_WR_QSPI = 0xE013
            
#         self.BLK_SIZE= 512
#         self.header = 0xE0
#         self.response_header = 0xE1
#         self.dev_id = 0x3E
#         self.dev_no = 0xFF    
#         self.footer1 = 0xFF
#         self.footer2 = 0xFE   
        
#         self.last_cmd = []
    
#     def set_port(self, ser_port):
#         self.ser = ser_port
        
#     def write_packet(self, cmd):
#         if(self.ser!=None): 
#             self.ser.flushInput()
#             self.ser.flushOutput()
#             self.ser.write(bytearray(cmd))
#             print("Command : ",[hex(i) for i in cmd])
#             self.last_cmd = cmd
#             with open(cmd_log_file, 'a+') as f:
#                 f.write('\n COMND : \t')
#                 for byte in cmd:
#                     f.write(hex(byte) + ", ")

#     def read_packet(self):
#         rt_cnt  = 0
#         rt_max  = 10 
        
#         rd_header   = 0
#         rd_sequence = 0
#         rd_dev_id   = 0
#         rd_dev_num  = 0
#         rd_length   = 0
#         rd_cmd_id   = 0
#         rd_cmd_type = 0
        
#         if(self.ser==None):
#             return 
        
#         rd_cmd0 = bytearray (self.ser.read(5)) 
#         if(len(rd_cmd0)!=5):
#             return -1, None 

#         while(1):
            
#             if(rt_cnt > rt_max): # return if max number of tries over
#                 return -1, None 
            
#             rd_header   = rd_cmd0[0]
#             rd_sequence = rd_cmd0[2] + (rd_cmd0[1] << 8)
#             rd_dev_id   = rd_cmd0[3]
#             rd_dev_num  = rd_cmd0[4]
            
#             if(rd_header == self.response_header\
#                and rd_sequence == self.sequence\
#                and rd_dev_id   == self.dev_id\
#                and rd_dev_num  == self.dev_no ):
                
#                 break
            
#             print("\n\nRESPONSE  : ", [hex(i) for i in rd_cmd0])
            
#             print("\nRECEIVED HEADER")
#             print("rd_header   : ",hex(rd_header))
#             print("rd_sequence : ",hex(rd_sequence))
#             print("rd_dev_id   : ",hex(rd_dev_id))
#             print("rd_dev_name : ",hex(rd_dev_num))
            
#             print("\nEXPECTED Header")
#             print("rd_header   : ",hex(self.response_header))
#             print("rd_sequence : ",hex(self.sequence))
#             print("rd_dev_id   : ",hex(self.dev_id))
#             print("rd_dev_name : ",hex(self.dev_no ))
            
#             rd_cmd1 = self.ser.read(1) 
#             if(len(rd_cmd1)!=1):
#                 return -1, None # return if buffer doesn't have any data
                    
#             temp_rrd_cmd0 = rd_cmd0
#             rd_cmd0 = temp_rrd_cmd0[1:] + rd_cmd1
            
#             rt_cnt = rt_cnt +1
         
#         rd_cmd2 = self.ser.read(1) 
#         if(len(rd_cmd2) != 1):
#             return -1, None 
        
#         rd_length = rd_cmd2[0]
        
#         expected_bytes_avail = rd_length+3
#         rd_cmd3 = self.ser.read(expected_bytes_avail)
        
#         if(len(rd_cmd3) != expected_bytes_avail):
#             return -1, None
        
#         rd_csm     = rd_cmd3[-3]
#         rd_footer1 = rd_cmd3[-2]
#         rd_footer2 = rd_cmd3[-1]
        
#         rd_cmd_type  = rd_cmd3[0]
#         rd_cmd_id    = rd_cmd3[3] + (rd_cmd3[2] << 8)  

#         crc = 0
#         crc = crc + rd_dev_id + rd_dev_num + rd_length
#         for data in rd_cmd3 [0: -3]:            
#             crc = crc + data
#         crc = crc%256
        
#         response = rd_cmd0 + rd_cmd2 + rd_cmd3
#         with open(cmd_log_file, 'a+') as f:
#             f.write('\n REPLY : \t')
#             for byte in response:
#                 f.write(hex(byte) + ", ")

#         if(rd_csm == crc\
#            and rd_footer1  == self.footer1\
#            and rd_footer2  == self.footer2\
#            and rd_cmd_id   == self.mem_cmd_id\
#            and rd_cmd_type == self.mem_cmd_type):
            
#             print("response : ", [hex(i) for i in rd_cmd0 + rd_cmd2 + rd_cmd3])
                        
#             return 0, rd_cmd0 + rd_cmd2 + rd_cmd3
#         print("\n\nCOMMAND SEND       : ", [hex(i) for i in self.last_cmd])
#         print("CORRUPTED RESPONSE  : ", [hex(i) for i in rd_cmd0 + rd_cmd2 + rd_cmd3])
#         print("\nRECEIVED Footer ERROR ")       
#         print("rd_cmd_id    : ",hex(rd_cmd_id))
#         print("rd_cmd_type  : ",hex(rd_cmd_type))
#         print("rd_csm       : ",hex(rd_csm))
#         print("rd_footer1   : ",hex(rd_footer1))
#         print("rd_footer2   : ",hex(rd_footer2))        
#         print("\nEXPECTED Footer")        
#         print("rd_cmd_id    : ",hex(self.mem_cmd_id)) 
#         print("rd_cmd_type  : ",hex(self.mem_cmd_type))
#         print("rd_csm       : ",hex(crc))
#         print("rd_footer1   : ",hex(self.footer1))
#         print("rd_footer2   : ",hex(self.footer2))
        
#         with open(cmd_log_file, 'a+') as f:
#             f.write("\n\nCORRUPTED RESPONSE  : ")
#             f.write("\nRECEIVED Footer ERROR ")       
#             f.write("\nrd_cmd_id    : "+str(hex(rd_cmd_id)))
#             f.write("\nrd_cmd_type  : "+str(hex(rd_cmd_type)))
#             f.write("\nrd_csm       : "+str(hex(rd_csm)))
#             f.write("\nrd_footer1   : "+str(hex(rd_footer1)))
#             f.write("\nrd_footer2   : "+str(hex(rd_footer2))) 
            
#             f.write("\n\nEXPECTED Footer")        
#             f.write("\nrd_cmd_id    : "+str(hex(self.mem_cmd_id))) 
#             f.write("\nrd_cmd_type  : "+str(hex(self.mem_cmd_type)))
#             f.write("\nrd_csm       : "+str(hex(crc)))
#             f.write("\nrd_footer1   : "+str(hex(self.footer1)))
#             f.write("\nrd_footer2   : "+str(hex(self.footer2)))
#             f.write("\n")
        
#         return -1, None
           
#     def send_receive_response(self, cmd, retry=2):
#         for i in range(retry):            
#             self.write_packet(cmd)
#             self.logger.debug([hex(i) for i in cmd])            
#             status, rd_cmd = self.read_packet()
       
#             response = {}
#             if(status==0):
#                 response['data'] = []
#                 if(self.idd=='old'):
#                     response['header'] = rd_cmd[0]
#                     response['packet_sequence'] = 0
#                     response['device_id'] = rd_cmd[1]
#                     response['device_number'] = rd_cmd[2]
#                     response['cmd_type'] = 0x57
#                     response['cmd'] = (rd_cmd[4] <<8 | rd_cmd[3])
#                     if(response['cmd']==0xDEAD):
#                         response['cmd_status'] = 1
#                     else:
#                         response['cmd_status'] = 0
#                     response['length'] = (rd_cmd[6] <<8 | rd_cmd[5])
#                     for i in range(response['length']):
#                         response['data'].append(rd_cmd[i+7])
#                     response['chksum'] = rd_cmd[response['length']+1]
#                     response['footer1'] = 255
#                     response['footer2'] = 255
#                 else:
#                     response['header'] = rd_cmd[0]
#                     response['packet_sequence'] = (rd_cmd[1]<<8 | rd_cmd[2])
#                     response['device_id'] = rd_cmd[3]
#                     response['device_number'] = rd_cmd[4]
#                     response['length'] = rd_cmd[5]
#                     response['cmd_type'] = rd_cmd[6]
#                     response['cmd_status'] = rd_cmd[7]
#                     response['cmd'] = (rd_cmd[8] <<8 | rd_cmd[9])
#                     for i in range(response['length']-4):
#                         response['data'].append(rd_cmd[i+10])
#                     response['chksum'] = rd_cmd[-3]
#                     response['footer1'] = rd_cmd[-2]
#                     response['footer2'] = rd_cmd[-1]
               
#                 self.logger.debug([hex(i) for i in rd_cmd])
#                 return response 
#             else:
#                 self.logger.warning('Read Unsuccessful')
                
#         self.logger.critical('Communication Link seems to be broken')
#         return None
     
#     def con_cmd(self, cmd, cmd_type, length, data):        
#         pkt =[]
#         pkt.append(self.header)
#         self.sequence += 1
#         self.mem_cmd_id = cmd
#         self.mem_cmd_type = cmd_type
        
#         if(self.idd=='old'):
#             pkt.append(self.dev_id)
#             pkt.append(self.dev_no)
#             pkt.append(cmd & 0xFF)
#             pkt.append(cmd>>8)
#             pkt.append(length & 0xFF)
#             pkt.append(length >> 8)
#             if(length!=0):
#                 pkt.extend(data)
            
#             crc = 0
#             for i in range(len(pkt)-1):
#                 crc=crc+pkt[i+1]
#             crc = crc%256
#             crc = ~crc & 0xFF
#             crc = (crc+1)%256
#             return pkt+[crc]
        
#         else:
#             pkt.append((self.sequence >> 8) & 0xFF)
#             pkt.append((self.sequence & 0xFF))
#             pkt.append(self.dev_id)
#             pkt.append(self.dev_no)
#             pkt.append((length+3) & 0xFF)
#             pkt.append(cmd_type)
#             pkt.append(cmd>>8)
#             pkt.append(cmd & 0xFF)
#             if(length!=0):
#                 pkt.extend(data)
            
#             crc = 0
#             for i in range(len(pkt)-1-2):
#                 crc=crc+pkt[i+1+2]
#             crc = crc%256
#             return pkt+[crc, self.footer1, self.footer2]

#     def fpga_read(self, addr):
#         self.logger.info('Reading FPGA register 0x%x' % (addr))
#         cmd = self.FPGA_RD_REGS | (addr & 0xFFF)
#         cmd_type = 0x52
#         length = 0
#         data = []
#         packet = self.con_cmd(cmd, cmd_type, length, data)
#         response = self.send_receive_response(packet)
#         return response

#     def fpga_write(self, addr, data):
#         self.logger.info('Writing to FPGA register, 0x%x=0x%x' % (addr, data))
#         cmd = self.FPGA_WR_REGS | (addr & 0xFFF)
#         cmd_type = 0x57
#         length = 4
#         data = self.split_num(data, split_way=4, endian=0)
#         packet = self.con_cmd(cmd, cmd_type, length, data)
#         response = self.send_receive_response(packet)
#         return response

#     def split_num(self, data, split_way=4, endian=0):
#         l = []
#         mask = 0xFF
#         for i in range(split_way):
#             l.append((data & (mask << (8 * i))) >> (8 * i))
#         return l[::-1] if endian == 0 else l

# if __name__ == '__main__':
#     # Use environment variable for port, defaulting to 8000 if not set
#     port = int(os.environ.get('PORT', 8000))
#     # In production, you typically want to set debug to False
#     app.run(host='0.0.0.0', port=port, debug=False)


from flask import Flask, request, render_template_string

app = Flask(__name__)

# Define the HTML template
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Calculator</title>
</head>
<body>
    <h1>Simple Calculator</h1>
    <form method="POST">
        <label for="num1">Number 1:</label>
        <input type="number" id="num1" name="num1" required>
        <br><br>
        <label for="num2">Number 2:</label>
        <input type="number" id="num2" name="num2" required>
        <br><br>
        <input type="submit" value="Add">
    </form>
    
    {% if result is not none %}
        <h2>Result: {{ result }}</h2>
    {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def calculator():
    result = None
    if request.method == 'POST':
        # Get the two numbers from the form
        num1 = request.form.get('num1', type=float)
        num2 = request.form.get('num2', type=float)
        
        # Perform the addition
        result = num1 + num2
    
    # Render the template and pass the result (if any)
    return render_template_string(html_template, result=result)

if __name__ == '__main__':
    app.run(debug=True)
