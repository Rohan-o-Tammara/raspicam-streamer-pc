import subprocess
import nmap

# The scanning method
def scan():
    pi_ip = [] #list holding all the IPs
    i = 0

    # run > ipconfig
    cmd = subprocess.Popen(['ipconfig'], stdout=subprocess.PIPE)
    det = cmd.stdout.read().decode('utf-8')

    #look for index of 'Wi-Fi' in output
    i_det = det.find('Wi-Fi')
    det2 = det[i_det:]

    #look for the system ip address in wi-fi segment and extract subnet of ip
    i_det2 = det2.find('IPv4 Address. . . . . . . . . . . : ')
    my_ip = det2[i_det2+36:i_det2+51]
    if my_ip[:10].count('.') == 3:
        subnet = my_ip[:10]+'*'
    elif my_ip[:11].count('.') == 3:
        subnet = my_ip[:11]+'*'
    elif my_ip[:12].count('.') == 3:
        subnet = my_ip[:12]+'*'

    print('Scanning...\n')

    #initialise nmap and scan for devices
    nm = nmap.PortScanner()
    nm.scan(subnet, '8080')

    # look for Raspberry pi using hostname
    all_hosts = nm.all_hosts()
    for host in all_hosts:
        cmd = subprocess.Popen(['nmap', host], stdout=subprocess.PIPE)
        shout = cmd.stdout.read().decode('utf-8')
        if 'Raspberry Pi' in shout and nm[host].state() == 'up':
            i += 1
            print('Found a Live Pi(Pi_'+str(i)+') at ', host, '\n')
            pi_ip.append(('Pi_'+ str(i) , host))
        if all_hosts.index(host) == len(all_hosts)-1 and len(pi_ip) == 0:
            print("No Raspberry Pi found.")

    '''
    cmd = subprocess.Popen(['nmap', '-p', '8080', '-sN', subnet], stdout=subprocess.PIPE)
    shout = cmd.stdout.read().decode('utf-8')
    print(shout)
    if 'Raspberry Pi' in shout:
        i = shout.index('Raspberry Pi')
        j = i - 147
        pi_ip.append(shout[i-148:i-132])
        print(i-j)
    '''

    print('Scan complete.\n')
    if len(pi_ip) != 0:
        return pi_ip
    else:
        pass
