// Sicht in Gebaeuden, Schritt 2: Dunkelheit in Vertex-Farbe x _Color.
// _StencilComp 6 (NotEqual) = nur ausserhalb der sichtbaren Flaeche (die schwarze Flaeche),
// _StencilComp 8 (Always)   = ueberall (Verlauf, der den Blick nach draussen mit der Entfernung abdunkelt).
Shader "Nightward/Vision Darkness"
{
    Properties
    {
        _Color ("Farbe", Color) = (0, 0, 0, 1)
        [Enum(UnityEngine.Rendering.CompareFunction)] _StencilComp ("Stencil Vergleich", Float) = 6
    }
    SubShader
    {
        Tags { "Queue" = "Transparent" "RenderType" = "Transparent" "RenderPipeline" = "UniversalPipeline" "IgnoreProjector" = "True" }
        Pass
        {
            ZWrite Off
            ZTest Always
            Cull Off
            Blend SrcAlpha OneMinusSrcAlpha
            Stencil
            {
                Ref 128
                ReadMask 128
                Comp [_StencilComp]
            }

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; half4 color : COLOR; };
            struct Varyings { float4 positionCS : SV_POSITION; half4 color : COLOR; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.color = v.color * _Color;
                return o;
            }

            half4 frag(Varyings i) : SV_Target { return i.color; }
            ENDHLSL
        }
    }
}
