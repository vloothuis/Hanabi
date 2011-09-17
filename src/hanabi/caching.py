def conditional_get(controller, response):
    """Require that the client revalidates."""
    response.headers['Cache-Control'] = 'must-revalidate'
    return response

def no_store(controller, response):
    """Do not allow the client to store the request.

    Please note that this is only useful for cases where security of the data
    might be a problem. This policy can seriously hurt performance in
    browsers (back button). Consider using the conditional_get policy instead.
    """
    response.headers['Cache-Control'] = 'no-store'
    return response
