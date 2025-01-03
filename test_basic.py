import dns.resolver

def test_1(dnsserver):
    r = dns.resolver.Resolver(configure=False)
    r.nameservers = ['127.0.0.1']
    r.port = dnsserver['port']

    a = r.resolve('ipv4.example.com')
    print(a)
