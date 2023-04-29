from octorest import OctoRest



def make_client(url, apikey):
    """Creates and returns an instance of the OctoRest client.

    Args:
        url - the url to the OctoPrint server
        apikey - the apikey from the OctoPrint server found in settings
    """
    try:
        client = OctoRest(url=url, apikey=apikey)
        return client
    except ConnectionError as ex:
        # Handle exception as you wish
        print(ex)

client = make_client("http://prusaprinter.local", "572323F7CF4749F4BD2DCC610E443C0E")
#client.jog moves print axis
client.connect()
client.jog(x= 5)

#does this works