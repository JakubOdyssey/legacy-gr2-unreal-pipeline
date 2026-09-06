/* Original independent-reader harness. ufbx is separately pinned MIT source.
 * Never reads GR2, never invokes a Granny library, never loads external files. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ufbx.h"
static FILE *out;
static void str(ufbx_string s) { fputc('"',out); for(size_t i=0;i<s.length;i++){ unsigned char c=s.data[i]; if(c=='"'||c=='\\'){fputc('\\',out);fputc(c,out);}else if(c<32)fprintf(out,"\\u%04x",c);else fputc(c,out);} fputc('"',out); }
static void v3(ufbx_vec3 v){fprintf(out,"[%.17g,%.17g,%.17g]",v.x,v.y,v.z);}
static void mat(ufbx_matrix m){fputc('[',out);for(int r=0;r<4;r++){if(r)fputc(',',out);fputc('[',out);for(int c=0;c<4;c++){if(c)fputc(',',out);fprintf(out,"%.17g",r==3?(double)(c==3):m.cols[c].v[r]);}fputc(']',out);}fputc(']',out);}
static void nodes(ufbx_scene *s){
    fputc('[',out);for(size_t i=0;i<s->nodes.count;i++){ufbx_node*n=s->nodes.data[i];if(i)fputc(',',out);fprintf(out,"{\"name\":");str(n->name);fprintf(out,",\"bone\":%s,\"is_root\":%s,\"parent\":",n->bone?"true":"false",n->is_root?"true":"false");if(n->parent&&!n->parent->is_root)str(n->parent->name);else fprintf(out,"null");fprintf(out,",\"local_matrix\":");mat(n->node_to_parent);fprintf(out,",\"world_matrix\":");mat(n->node_to_world);fprintf(out,",\"rotation_xyzw\":[%.17g,%.17g,%.17g,%.17g],\"scale\":",n->local_transform.rotation.x,n->local_transform.rotation.y,n->local_transform.rotation.z,n->local_transform.rotation.w);v3(n->local_transform.scale);fprintf(out,",\"has_adjust_transform\":%s,\"inherit_mode\":%d}",n->has_adjust_transform?"true":"false",(int)n->inherit_mode);}fputc(']',out);
}
static void meshes(ufbx_scene*s){
    fputc('[',out);for(size_t i=0;i<s->meshes.count;i++){
        ufbx_mesh*m=s->meshes.data[i];if(i)fputc(',',out);fprintf(out,"{\"name\":");str(m->name);fprintf(out,",\"num_vertices\":%zu,\"num_triangles\":%zu,\"positions\":[",m->num_vertices,m->num_triangles);
        for(size_t j=0;j<m->vertices.count;j++){if(j)fputc(',',out);v3(m->vertices.data[j]);}fprintf(out,"],\"indices\":[");
        for(size_t j=0;j<m->vertex_indices.count;j++){if(j)fputc(',',out);fprintf(out,"%u",m->vertex_indices.data[j]);}fprintf(out,"],\"normals_by_corner\":[");
        for(size_t j=0;j<m->num_indices;j++){if(j)fputc(',',out);v3(ufbx_get_vertex_vec3(&m->vertex_normal,j));}fprintf(out,"],\"uvs_by_corner\":[");
        for(size_t j=0;j<m->num_indices;j++){if(j)fputc(',',out);ufbx_vec2 v=ufbx_get_vertex_vec2(&m->vertex_uv,j);fprintf(out,"[%.17g,%.17g]",v.x,v.y);}fprintf(out,"],\"face_material\":[");
        for(size_t j=0;j<m->face_material.count;j++){if(j)fputc(',',out);fprintf(out,"%u",m->face_material.data[j]);}fprintf(out,"],\"materials\":[");
        for(size_t j=0;j<m->materials.count;j++){if(j)fputc(',',out);str(m->materials.data[j]->name);}fprintf(out,"],\"clusters\":[");
        int comma=0;for(size_t di=0;di<m->skin_deformers.count;di++){ufbx_skin_deformer*d=m->skin_deformers.data[di];for(size_t ci=0;ci<d->clusters.count;ci++){
            ufbx_skin_cluster*c=d->clusters.data[ci];if(comma++)fputc(',',out);fprintf(out,"{\"bone\":");str(c->bone_node->name);fprintf(out,",\"inverse_bind\":");mat(c->geometry_to_bone);fprintf(out,",\"weights\":[");
            for(size_t wi=0;wi<c->vertices.count;wi++){if(wi)fputc(',',out);fprintf(out,"[%u,%.17g]",c->vertices.data[wi],c->weights.data[wi]);}fprintf(out,"]}");
        }}fprintf(out,"]}");
    }fputc(']',out);
}
int main(int argc,char**argv){
    if(argc<3||argc>4){fprintf(stderr,"Usage: ufbx_audit input.fbx output.json [times.txt]\n");return 2;}
    ufbx_load_opts opts={0};opts.load_external_files=false;opts.clean_skin_weights=false;opts.strict=true;opts.disable_quirks=true;opts.force_single_thread_ascii_parsing=true;
    ufbx_error error;ufbx_scene*s=ufbx_load_file(argv[1],&opts,&error);
    if(!s){char msg[4096];ufbx_format_error(msg,sizeof(msg),&error);fprintf(stderr,"%s\n",msg);return 3;}
    out=fopen(argv[2],"wb");if(!out)return 4;
    fprintf(out,"{\"reader\":\"ufbx pinned locally compiled\",\"bone_count\":%zu,\"nodes\":",s->bones.count);nodes(s);fprintf(out,",\"meshes\":");meshes(s);
    fprintf(out,",\"textures\":[");for(size_t i=0;i<s->textures.count;i++){if(i)fputc(',',out);ufbx_texture*t=s->textures.data[i];fprintf(out,"{\"name\":");str(t->name);fprintf(out,",\"filename\":");str(t->filename);fprintf(out,",\"relative_filename\":");str(t->relative_filename);fprintf(out,"}");}
    fprintf(out,"],\"warnings\":[");for(size_t i=0;i<s->metadata.warnings.count;i++){if(i)fputc(',',out);ufbx_warning*w=&s->metadata.warnings.data[i];fprintf(out,"{\"type\":%d,\"count\":%zu,\"description\":",(int)w->type,w->count);str(w->description);fprintf(out,"}");}
    fprintf(out,"],\"animations\":[");for(size_t i=0;i<s->anim_stacks.count;i++){if(i)fputc(',',out);ufbx_anim_stack*a=s->anim_stacks.data[i];fprintf(out,"{\"name\":");str(a->name);fprintf(out,",\"start\":%.17g,\"end\":%.17g}",a->time_begin,a->time_end);}
    fprintf(out,"],\"frames\":[");
    if(argc==4){FILE*times=fopen(argv[3],"rb");if(!times)return 5;double t;int first=1;ufbx_evaluate_opts eval={0};eval.load_external_files=false;while(fscanf(times,"%lf",&t)==1){ufbx_scene*es=ufbx_evaluate_scene(s,s->anim_stacks.count?s->anim_stacks.data[0]->anim:s->anim,t,&eval,&error);if(!es){fprintf(stderr,"Evaluation failed\n");return 6;}if(!first)fputc(',',out);first=0;fprintf(out,"{\"time_seconds\":%.17g,\"nodes\":",t);nodes(es);fprintf(out,"}");ufbx_free_scene(es);}fclose(times);}
    fprintf(out,"]}\n");fclose(out);ufbx_free_scene(s);return 0;
}
