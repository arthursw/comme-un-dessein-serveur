define([], function() {
    return shader = `

varying vec2 vUv;

uniform float time;
uniform bool label;

uniform sampler2D textureSampler;
uniform vec2 screenResolution;
uniform vec2 textureResolution;

uniform float hue;
uniform float saturation;
uniform float lightness;

uniform vec3 colors[7];

#define PI 3.1415926535897932384626433832795
#define TWO_PI 2.0 * PI

int modulo(int i, int m) {
    return i - m * (i / m);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

vec4 hsv2rgb(vec4 c) {
    return vec4(hsv2rgb(c.xyz), c.w);
}

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec4 rgb2hsv(vec4 c) {
    return vec4(rgb2hsv(c.xyz), c.w);
}

vec4 preprocess(vec4 c) {
    vec4 chsv = rgb2hsv(c);
    chsv.x = mod(chsv.x + hue, 1.0);
    chsv.y += saturation;
    chsv.z += lightness;
    return hsv2rgb(chsv);
}

vec4 rgb2cmyk(vec3 rgb) {

    float k = 1.0 - max(rgb.r, max(rgb.g, rgb.b) );
    float f = k < 1.0 ? 1.0 / (1.0 - k) : 0.0;
    float c = (1.0 - rgb.r - k) * f;
    float m = (1.0 - rgb.g - k) * f;
    float y = (1.0 - rgb.b - k) * f;

    return vec4(c, m, y, k);
}

vec3 cmyk2rgb(vec4 cmyk) {
    float c = cmyk.r;
    float m = cmyk.g;
    float y = cmyk.b;
    float k = cmyk.a;

    return vec3(k >= 1.0 || c >= 1.0 ? 0.0 : (1.0 - c) * (1.0 - k),
                k >= 1.0 || m >= 1.0 ? 0.0 : (1.0 - m) * (1.0 - k),
                k >= 1.0 || k >= 1.0 ? 0.0 : (1.0 - y) * (1.0 - k) );
}

vec3 rgb2xyz(vec3 rgb) {
    rgb.r = rgb.r > 0.04045 ? pow( ( rgb.r + 0.055 ) / 1.055, 2.4) : rgb.r / 12.92;
    rgb.g = rgb.g > 0.04045 ? pow( ( rgb.g + 0.055 ) / 1.055, 2.4) : rgb.g / 12.92;
    rgb.b = rgb.b > 0.04045 ? pow( ( rgb.b + 0.055 ) / 1.055, 2.4) : rgb.b / 12.92;

    rgb *= 100.0;

    return vec3(rgb.r * 0.4124 + rgb.g * 0.3576 + rgb.b * 0.1805, 
                rgb.r * 0.2126 + rgb.g * 0.7152 + rgb.b * 0.0722, 
                rgb.r * 0.0193 + rgb.g * 0.1192 + rgb.b * 0.9505);
}


vec3 xyz2lab(vec3 xyz) {
    xyz = xyz / vec3(94.811, 100.000, 107.304);
    
    xyz = vec3( xyz.r > 0.008856 ? pow( xyz.r, 1.0/3.0) : (7.787 * xyz.r) + (16.0 / 116.0),
                xyz.g > 0.008856 ? pow( xyz.g, 1.0/3.0) : (7.787 * xyz.g) + (16.0 / 116.0),
                xyz.b > 0.008856 ? pow( xyz.b, 1.0/3.0) : (7.787 * xyz.b) + (16.0 / 116.0));

    return vec3( (116.0 * xyz.y) - 16.0, 500.0 * (xyz.x - xyz.y), 200.0 * (xyz.y - xyz.z) );
}

vec3 rgb2lab(in vec3 rgb) {
    vec3 xyz = rgb2xyz(rgb);
    vec3 lab = xyz2lab(xyz);
    return(lab);
}

float colorDifferenceCIE94FromLab(vec3 cieLab1, vec3 cieLab2) {

    // Just to make it more readable
    float cL1 = cieLab1.r;
    float ca1 = cieLab1.g;
    float cb1 = cieLab1.b;

    float cL2 = cieLab2.r;
    float ca2 = cieLab2.g;
    float cb2 = cieLab2.b;

    float c1 = sqrt(ca1 * ca1 + cb1 * cb1);
    float c2 = sqrt(ca2 * ca2 + cb2 * cb2);
    
    float dL = cL2 - cL1;

    float dC = c2 - c1;

    float dE = sqrt( (cL1 - cL2) * (cL1 - cL2) + (ca1 - ca2) * (ca1 - ca2) + (cb1 - cb2) * (cb1 - cb2) );

    float dH = (dE * dE) - (dL * dL) - (dC * dC);

    dH = dH > 0.0 ? sqrt(dH) : 0.0;

    float kL = 1.0;
    float kC = 1.0;
    float kH = 1.0;
    float k1 = 0.045;
    float k2 = 0.015;

    float sL = 1.0;
    float sC = 1.0 + ( k1 * c1 ); // sX
    float sH = 1.0 + ( k2 * c1 ); // sH

    float dLw = dL / (kL * sL);
    float dCw = dC / (kC * sC);
    float dHw = dH / (kH * sH);

    float deltaE94 = sqrt(dLw * dLw + dCw * dCw + dHw * dHw);

    return deltaE94;
}

float colorDifferenceCIE94FromRGB(vec3 rgb1, vec3 rgb2) {
    vec3 lab1 = rgb2lab(rgb1);
    vec3 lab2 = rgb2lab(rgb2);
    return colorDifferenceCIE94FromLab(lab1, lab2);
}

vec3 getClosestColor(vec3 pixel) {

    float minDistance = 1000000.0;

    int index = 0;
    vec3 color = colors[0];
    
    float distance = colorDifferenceCIE94FromRGB(pixel, colors[0]);
    if(distance < minDistance) {
        index = 0;
        minDistance = distance;
        color = colors[0];
    }
    distance = colorDifferenceCIE94FromRGB(pixel,  colors[1]);
    if(distance < minDistance) {
        index = 1;
        minDistance = distance;
        color = colors[1];
    }
    distance = colorDifferenceCIE94FromRGB(pixel, colors[2]);
    if(distance < minDistance) {
        index = 2;
        minDistance = distance;
        color = colors[2];
    }
    distance = colorDifferenceCIE94FromRGB(pixel, colors[3]);
    if(distance < minDistance) {
        index = 3;
        minDistance = distance;
        color = colors[3];
    }
    distance = colorDifferenceCIE94FromRGB(pixel, colors[4]);
    if(distance < minDistance) {
        index = 4;
        minDistance = distance;
        color = colors[4];
    }
    distance = colorDifferenceCIE94FromRGB(pixel,  colors[5]);
    if(distance < minDistance) {
        index = 5;
        minDistance = distance;
        color = colors[5];
    }
    distance = colorDifferenceCIE94FromRGB(pixel,  colors[6]);
    if(distance < minDistance) {
        index = 6;
        minDistance = distance;
        color = colors[6];
    }
    return color;
}

void main() {

    float screenRatio = screenResolution.x / screenResolution.y;
    vec2 uv = gl_FragCoord.xy / screenResolution.xy;

    uv -= 0.5;
    uv = screenRatio > 1. ? vec2(uv.x * screenRatio, uv.y) : vec2(uv.x, uv.y / screenRatio);

    vec3 pixel = preprocess(texture2D(textureSampler, vUv)).xyz;

    vec3 color = colors[0];
    int index;
    float minDistance = 1000000.0;
    
    float distance = colorDifferenceCIE94FromRGB(pixel, colors[0]);

    if(distance < minDistance) {
        index = 0;
        minDistance = distance;
        color = colors[0];
    }
    distance = colorDifferenceCIE94FromRGB(pixel,  colors[1]);
    if(distance < minDistance) {
        index = 1;
        minDistance = distance;
        color = colors[1];
    }
    distance = colorDifferenceCIE94FromRGB(pixel, colors[2]);
    if(distance < minDistance) {
        index = 2;
        minDistance = distance;
        color = colors[2];
    }
    distance = colorDifferenceCIE94FromRGB(pixel, colors[3]);
    if(distance < minDistance) {
        index = 3;
        minDistance = distance;
        color = colors[3];
    }
    distance = colorDifferenceCIE94FromRGB(pixel, colors[4]);
    if(distance < minDistance) {
        index = 4;
        minDistance = distance;
        color = colors[4];
    }
    distance = colorDifferenceCIE94FromRGB(pixel,  colors[5]);
    if(distance < minDistance) {
        index = 5;
        minDistance = distance;
        color = colors[5];
    }
    distance = colorDifferenceCIE94FromRGB(pixel,  colors[6]);
    if(distance < minDistance) {
        index = 6;
        minDistance = distance;
        color = colors[6];
    }

	// float y = mod(vUv.y, 0.2) < 0.1 ? 1. : 0.;
    float n = 10.0;
    float i = 1.0 / n;
    // gl_FragColor = mod(vUv.y, i) < 0.5 * i ? vec4(color, 1.0) : pixel;
    float l = float(index) / 255.0;
    gl_FragColor = label ? vec4(l, l, l, 1.0) : vec4(color, 1.0);
}`});
