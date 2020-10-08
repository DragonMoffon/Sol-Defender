#version 330

//the length of time the burst has existed
uniform float time;

//the position modifier to allow the trail to follow the enemy
uniform vec2 pos;

//the initial position of the burst
in vec2 in_pos;

in vec2 in_vel;

in float in_fade;

out vec4 color;

void main() {

    float alpha = 1 - (in_fade * time);
    if(alpha < 0.0) alpha = 0;

    // 0.608, 0.749, 0.141
    color = vec4(0.00, 0.76, 1.00, alpha);

    vec2 mod_pos = pos + (in_vel * time);

    gl_Position = vec4(mod_pos, 0.0, 1);
}