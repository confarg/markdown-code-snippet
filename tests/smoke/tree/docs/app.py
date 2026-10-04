def main():
    setup()
    # [snippet: body]
    config = load()
    run(config)
    # [/snippet]
    teardown()
