systemContext platform "context" "The platform, the people who use it and the external systems it works with." {
    include *
    // Connected to the platform only through other external systems.
    include dataConsumer containerRegistry
    autoLayout lr
}
