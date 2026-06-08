// 1. Para la utilización del Límite Internacional en mapas web es necesario incluir la siguiente reserva:
// “La representación del Límite Internacional ha sido autorizada para una escala 1:50.000 cualquier representación a escalas mayores puede no corresponder completamente al trazado de los límites oficiales”
// 2. Es importante mencionar que la disponibilización y entrega del presente Límite Internacional, y cualquier utilización que se haga del mismo no implica bajo ninguna circunstancia la aprobación para la circulación de cualquier obra que represente el límite internacional, por lo que dicho material deberá ser remitido a esta Dirección Nacional según lo dispuesto en la normativa vigente para su revisión, edición, aprobación y circulación.
// 3. Para consultas, dirigirse a ugit@minrel.gob.cl

//Agregar variable de la ubicación en que se centrará el mapa
var mapCenter = [-37.5, -70.65];

//Agregar variable mapa y configuració de comienzo inicial de archivo html
var myMap = L.map('map').setView(mapCenter, 5);

// Agregar mapa base de OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(myMap);

// Agregar un control de escala personalizado al mapa 
L.control.scale({
    metric: true,
    imperial: false,
    maxWidth: 200,
    position: 'bottomleft', 
    updateWhenIdle: true,
    scaleWidth: 0.5,
    scaleRatio: 50000 
}).addTo(myMap);

// Agregar estilo de capa internacional 
var internacional_estilo ={
    "color": '#a45cc4',
    "weight":  8,
};

// Agregar estilo de capa internacional 2
var internacional_2_estilo ={
    "color": '#141414',
    "weight":  1,
    "dashArray": "1,5,10"
};

// Agregar estilo de capa internacionalzee
var internacionalzee_estilo ={
    "color": '#a45cc4',
    "weight":  8,
    "dashArray": "5, 10"
};

// Agregar estilo de capa internacionalzee_2
var internacionalzee_2_estilo ={
    "color": '#141414',
    "weight":  1,
    "dashArray": "5,10"
};

// Agregar estilo de capa internacionalrecuadro
var internacionalrecuadro_estilo ={
    "color": '#2a4159',
    "fillColor": "#a4bccc",
    "fillOpacity": "1"
};

// Agregar capa en formato GeoJson límite internacional con su respectivo estilo al mapa
L.geoJson(internacionalrecuadro, {style: internacionalrecuadro_estilo}).addTo(myMap);
L.geoJson(internacional, {style: internacional_estilo}).addTo(myMap);
L.geoJson(internacional_2, {style: internacional_2_estilo}).addTo(myMap);
L.geoJson(internacionalzee, {style: internacionalzee_estilo}).addTo(myMap);
L.geoJson(internacionalzee_2, {style: internacionalzee_2_estilo}).addTo(myMap);
