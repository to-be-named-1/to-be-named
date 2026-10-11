// Permanent styles. Temporary styles live in views/overlays/.
// Colour is never the only cue: shapes, borders and line styles carry each tag's meaning as well.
styles {
    element "Person" {
        shape Person
        background #08427b
        color #ffffff
    }
    element "Software System" {
        background #1168bd
        color #ffffff
    }
    element "Container" {
        background #438dd5
        color #ffffff
    }
    element "Component" {
        background #85bbf0
        color #000000
    }
    element "External" {
        background #999999
        color #ffffff
    }
    element "Database" {
        shape Cylinder
    }
    element "Web Browser" {
        shape WebBrowser
    }
    element "Maintenance unit" {
        shape Ellipse
    }
    element "Leader only" {
        shape Hexagon
    }
    element "Commercial" {
        stroke #b26a00
        strokeWidth 6
    }
    element "Extension point" {
        border dotted
    }
    relationship "Relationship" {
        style solid
    }
    relationship "Asynchronous" {
        style dashed
    }
}
