import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ApiService, Meta, PageResponse, readableError } from '../core/api';
interface Field {key:string;label:string;type?:'text'|'email'|'password'|'date'|'number'|'select'|'checkbox'|'textarea';source?:keyof Meta;required?:boolean}
interface ResourceConfig {title:string;description:string;columns:string[];fields:Field[];edit?:boolean;delete?:boolean}
const field=(key:string,label:string,type:Field['type']='text',required=false,source?:keyof Meta):Field=>({key,label,type,required,source});
const configs:Record<string,ResourceConfig>={
 students:{title:'Students',description:'All student profiles and admission records',columns:['code','full_name','email','class_id','batch_id','active'],fields:[field('full_name','Full Name','text',true),field('email','Email','email',true),field('password','Password (new account / optional on edit)','password'),field('class_id','Class','select',true,'classes'),field('batch_id','Batch','select',true,'batches'),field('father_name','Father’s Name'),field('mother_name','Mother’s Name'),field('gender','Gender'),field('dob','Date of Birth','date'),field('mobile','Mobile'),field('guardian_mobile','Guardian Mobile'),field('address','Address','textarea'),field('admission_date','Admission Date','date'),field('active','Active','checkbox')],delete:true},
 teachers:{title:'Teachers',description:'Faculty profiles and access',columns:['code','full_name','email','qualification','mobile','active'],fields:[field('full_name','Full Name','text',true),field('email','Email','email',true),field('password','Password (new account / optional on edit)','password'),field('qualification','Qualification'),field('mobile','Mobile'),field('address','Address','textarea'),field('joining_date','Joining Date','date'),field('active','Active','checkbox')],delete:true},
 classes:{title:'Classes',description:'Academic classes in your institute',columns:['name','description','active'],fields:[field('name','Class Name','text',true),field('description','Description','textarea'),field('active','Active','checkbox')],delete:true},
 batches:{title:'Batches',description:'Timetables and student groups',columns:['name','class_id','timings','start_date','active'],fields:[field('name','Batch Name','text',true),field('class_id','Class','select',true,'classes'),field('start_date','Start Date','date'),field('end_date','End Date','date'),field('timings','Timings'),field('active','Active','checkbox')],delete:true},
 subjects:{title:'Subjects',description:'Manage your teaching curriculum',columns:['name','description','active'],fields:[field('name','Subject Name','text',true),field('description','Description','textarea'),field('active','Active','checkbox')],delete:true},
 'class-subjects':{title:'Class Subjects',description:'Configure the subjects taught in each class',columns:['class_id','subject_id'],fields:[field('class_id','Class','select',true,'classes'),field('subject_id','Subject','select',true,'subjects')],edit:false,delete:false},
 'teacher-assignments':{title:'Teaching Assignments',description:'Authorize teachers to teach specific batch subjects',columns:['teacher_id','class_id','batch_id','subject_id'],fields:[field('teacher_id','Teacher','select',true,'teachers'),field('class_id','Class','select',true,'classes'),field('batch_id','Batch','select',true,'batches'),field('subject_id','Subject','select',true,'subjects')],delete:true},
 examinations:{title:'Examinations',description:'Create tests and control result publication',columns:['name','academic_year','class_id','batch_id','start_date','published'],fields:[field('name','Examination Name','text',true),field('academic_year','Academic Year','text',true),field('class_id','Class','select',true,'classes'),field('batch_id','Batch (optional)','select',false,'batches'),field('exam_type','Exam Type'),field('start_date','Start Date','date'),field('end_date','End Date','date'),field('description','Description','textarea'),field('published','Publish results to students','checkbox')],delete:true},
 'examination-subjects':{title:'Exam Subjects & Maximum Marks',description:'Set grading maxima and pass marks before entering results',columns:['examination_id','subject_id','max_marks','passing_marks'],fields:[field('examination_id','Examination','select',true,'examinations'),field('subject_id','Subject','select',true,'subjects'),field('max_marks','Maximum Marks','number',true),field('passing_marks','Passing Marks','number',true)],delete:true}
};
@Component({standalone:true,imports:[CommonModule,ReactiveFormsModule],template:`
<div class="page-heading"><div><span class="eyebrow">ACADEMIC MANAGEMENT</span><h1>{{config.title}}</h1><p>{{config.description}}</p></div><button class="btn btn-primary" (click)="openNew()"><i class="bi bi-plus-lg"></i> Add New</button></div>
@if(message()){<div class="alert" [class.alert-danger]="error()" [class.alert-success]="!error()">{{message()}}</div>}
<div class="panel"><div class="table-toolbar"><div class="search-box"><i class="bi bi-search"></i><input class="form-control" placeholder="Search records…" [value]="search()" (input)="changeSearch($event)"></div><span class="muted small">{{total()}} records</span></div>
<div class="table-responsive"><table class="table modern-table"><thead><tr>@for(col of config.columns; track col){<th>{{label(col)}}</th>}<th class="text-end">Actions</th></tr></thead><tbody>
@if(loading()){<tr><td [attr.colspan]="config.columns.length+1" class="empty-table">Loading records…</td></tr>}
@else if(!items().length){<tr><td [attr.colspan]="config.columns.length+1" class="empty-table"><i class="bi bi-inbox"></i><p>No records found. Add your first entry to get started.</p></td></tr>}
@else {@for(item of items(); track $index){<tr>@for(col of config.columns; track col){<td>{{display(item,col)}}</td>}
<td class="text-end text-nowrap">@if(config.edit!==false){<button class="btn btn-ghost btn-sm" (click)="openEdit(item)" title="Edit"><i class="bi bi-pencil"></i></button>}
@if(config.delete){<button class="btn btn-ghost btn-sm text-danger" (click)="remove(item)" title="Deactivate or remove"><i class="bi bi-trash"></i></button>}</td></tr>}}
</tbody></table></div><div class="pagination-line"><button class="btn btn-outline-secondary btn-sm" [disabled]="page()<=1" (click)="goPage(-1)">Previous</button><span>Page {{page()}} of {{maxPage()}}</span><button class="btn btn-outline-secondary btn-sm" [disabled]="page()>=maxPage()" (click)="goPage(1)">Next</button></div></div>
@if(editing()){<div class="modal-backdrop-custom" (click)="close()"><section class="edit-dialog" role="dialog" aria-modal="true" aria-label="Record editor" (click)="$event.stopPropagation()"><header><div><h3>{{selectedId()===null?'Add':'Edit'}} {{config.title}}</h3><p class="muted">Fields marked * are required.</p></div><button class="icon-button" (click)="close()"><i class="bi bi-x-lg"></i></button></header>
<form [formGroup]="form" (ngSubmit)="save()"><div class="form-grid">
@for(f of config.fields;track f.key){<div [class.full-span]="f.type==='textarea'"><label class="form-label">{{f.label}}{{f.required?' *':''}}</label>
@if(f.type==='select'){<select class="form-select" [formControlName]="f.key"><option value="">Select {{f.label}}</option>@for(opt of options(f);track opt.id){<option [value]="opt.id">{{opt.name}}</option>}</select>}
@else if(f.type==='checkbox'){<div class="form-check form-switch"><input class="form-check-input" type="checkbox" [formControlName]="f.key"><label class="form-check-label">Enabled</label></div>}
@else if(f.type==='textarea'){<textarea class="form-control" rows="2" [formControlName]="f.key"></textarea>}
@else{<input class="form-control" [type]="f.type||'text'" [formControlName]="f.key" [placeholder]="f.label" [step]="f.type==='number'?'0.01':null">}
</div>}
</div><footer><button type="button" class="btn btn-outline-secondary" (click)="close()">Cancel</button><button type="submit" class="btn btn-primary" [disabled]="saving()||form.invalid">{{saving()?'Saving…':'Save Record'}}</button></footer></form></section></div>}
`})
export class ManagePage implements OnInit{
 private api=inject(ApiService);private route=inject(ActivatedRoute);private fb=inject(FormBuilder);
 resource='students';config:ResourceConfig=configs['students'];form:FormGroup=this.fb.group({});
 items=signal<any[]>([]);meta=signal<Meta>({classes:[],batches:[],subjects:[],teachers:[],students:[],examinations:[]});
 total=signal(0);page=signal(1);loading=signal(false);editing=signal(false);saving=signal(false);selectedId=signal<number|null>(null);search=signal('');message=signal('');error=signal(false);
 ngOnInit(){this.route.paramMap.subscribe(params=>{const id=params.get('resource')||'students';this.resource=configs[id]?id:'students';this.config=configs[this.resource];this.page.set(1);this.load();this.loadMeta();});}
 label(k:string){return this.config.fields.find(f=>f.key===k)?.label||k.replaceAll('_',' ').replace(/\b\w/g,s=>s.toUpperCase());}
 options(f:Field):any[]{return f.source?this.meta()[f.source]:[];}
 display(item:any,key:string){const field=this.config.fields.find(f=>f.key===key);if(field?.source){const found=this.meta()[field.source].find((e:any)=>String(e.id)===String(item[key]));return found?.name||item[key]||'—';}if(typeof item[key]==='boolean')return item[key]?'Yes':'No';return item[key]??'—';}
 changeSearch(e:Event){this.search.set((e.target as HTMLInputElement).value);this.page.set(1);this.load();}
 maxPage(){return Math.max(1,Math.ceil(this.total()/20));}
 goPage(offset:number){this.page.update(n=>n+offset);this.load();}
 loadMeta(){this.api.get<Meta>('meta').subscribe({next:r=>this.meta.set(r),error:()=>{}});}
 load(){this.loading.set(true);this.api.get<PageResponse>(this.resource,{page:this.page(),size:20,q:this.search()}).subscribe({next:r=>{this.items.set(r.items);this.total.set(r.total);this.loading.set(false);},error:e=>{this.loading.set(false);this.notice(readableError(e),true);}});}
 newForm(item:any={}){const group:Record<string,any>={};for(const f of this.config.fields){const mandatory=f.required && !(f.key==='password'&&this.selectedId()!==null);group[f.key]=[f.key==='password'?'':(item[f.key]??(f.type==='checkbox'?true:'')),mandatory?[Validators.required]:[]];}this.form=this.fb.group(group);}
 openNew(){this.selectedId.set(null);this.newForm();this.editing.set(true);}
 openEdit(item:any){this.selectedId.set(item.id);this.newForm(item);this.editing.set(true);}
 close(){this.editing.set(false);}
 notice(msg:string,failed=false){this.message.set(msg);this.error.set(failed);}
 save(){if(this.form.invalid)return;this.saving.set(true);const values={...this.form.value};if(!values['password'])delete values['password'];
   const req=this.selectedId()===null?this.api.post<any>(this.resource,values):this.api.put<any>(`${this.resource}/${this.selectedId()}`,values);
   req.subscribe({next:()=>{this.saving.set(false);this.close();this.notice('Record saved successfully');this.load();this.loadMeta();},error:e=>{this.saving.set(false);this.notice(readableError(e),true);}});
 }
 remove(item:any){if(!item.id){this.notice('This record cannot be deleted from this view',true);return;}if(!confirm(`Remove/deactivate this ${this.config.title.toLowerCase()} record?`))return;
   this.api.delete(`${this.resource}/${item.id}`).subscribe({next:()=>{this.notice('Record updated');this.load();this.loadMeta();},error:e=>this.notice(readableError(e),true)});
 }
}
