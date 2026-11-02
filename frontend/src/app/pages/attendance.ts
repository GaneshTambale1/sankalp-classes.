import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, Meta, readableError } from '../core/api';
import { AuthService } from '../core/auth';
interface Row {student_id:number;name:string;code:string;status:'present'|'absent'|'leave'|''}
@Component({standalone:true,imports:[CommonModule,FormsModule],template:`
<div class="page-heading"><div><span class="eyebrow">DAILY TRACKING</span><h1>Attendance</h1><p>{{auth.role()==='student'?'Review your attendance record.':'Fast, accurate attendance for your batches.'}}</p></div></div>
@if(message()){<div class="alert" [class.alert-danger]="failed()" [class.alert-success]="!failed()">{{message()}}</div>}
@if(auth.role()==='student'){
<div class="stats-grid"><div class="stat-card"><small>Present Days</small><div class="stat-value">{{summary()?.present||0}}</div></div><div class="stat-card"><small>Absent Days</small><div class="stat-value">{{summary()?.absent||0}}</div></div><div class="stat-card"><small>Approved Leave</small><div class="stat-value">{{summary()?.leave||0}}</div></div><div class="stat-card"><small>Attendance Percentage</small><div class="stat-value">{{summary()?.percentage||0}}%</div></div></div>
<div class="panel"><h3>Attendance History</h3><div class="table-responsive"><table class="table modern-table"><thead><tr><th>Date</th><th>Status</th></tr></thead><tbody>@for(item of history();track item.id){<tr><td>{{item.date}}</td><td><span class="status-pill" [class.present]="item.status==='present'" [class.absent]="item.status==='absent'">{{item.status|titlecase}}</span></td></tr>}</tbody></table></div>@if(!history().length){<div class="empty-state">No attendance data yet.</div>}</div>
}@else{
<div class="panel filters-panel"><div class="filter-grid"><div><label class="form-label">Class</label><select class="form-select" [(ngModel)]="classId" (ngModelChange)="classChanged()"><option [ngValue]="0">Select class</option>@for(c of meta().classes;track c.id){<option [ngValue]="c.id">{{c.name}}</option>}</select></div><div><label class="form-label">Batch</label><select class="form-select" [(ngModel)]="batchId" (ngModelChange)="load()"><option [ngValue]="0">Select batch</option>@for(b of batches();track b.id){<option [ngValue]="b.id">{{b.name}}</option>}</select></div><div><label class="form-label">Attendance Date</label><input type="date" class="form-control" [(ngModel)]="attendanceDate" (ngModelChange)="load()"></div></div></div>
<div class="panel"><div class="panel-heading"><div><h3>Student Attendance</h3><small>{{rows().length}} students · {{attendanceDate}}</small></div><div class="toolbar-actions"><button class="btn btn-outline-primary btn-sm" (click)="allPresent()" [disabled]="!rows().length">Mark All Present</button><button class="btn btn-primary btn-sm" (click)="save()" [disabled]="busy()||!rows().length||hasUnmarked()">{{busy()?'Saving…':'Save Attendance'}}</button></div></div>
<div class="table-responsive"><table class="table modern-table"><thead><tr><th>Student</th><th>Student ID</th><th>Present</th><th>Absent</th><th>Leave</th></tr></thead><tbody>
@for(row of rows();track row.student_id){<tr><td><strong>{{row.name}}</strong></td><td>{{row.code}}</td>@for(st of statuses;track st){<td><label class="radio-button"><input type="radio" [name]="'attendance-'+row.student_id" [checked]="row.status===st" (change)="row.status=st"><span>{{st|titlecase}}</span></label></td>}</tr>}
</tbody></table></div>@if(!rows().length){<div class="empty-state">Choose a class and batch to load students.</div>}</div>
}
`})
export class AttendancePage implements OnInit{
 auth=inject(AuthService);private api=inject(ApiService);
 meta=signal<Meta>({classes:[],batches:[],subjects:[],teachers:[],students:[],examinations:[]});rows=signal<Row[]>([]);history=signal<any[]>([]);summary=signal<any>(null);
 statuses:['present','absent','leave']=['present','absent','leave'];classId=0;batchId=0;attendanceDate=new Date().toLocaleDateString('sv-SE');busy=signal(false);message=signal('');failed=signal(false);
 ngOnInit(){if(this.auth.role()==='student'){this.api.get<any>('dashboard/student').subscribe({next:r=>{if(r.student)this.api.get<any>(`attendance/student/${r.student.id}`).subscribe({next:x=>{this.history.set(x.items);this.summary.set(x.summary);}});},error:e=>this.notice(readableError(e),true)});}else{this.api.get<Meta>('meta').subscribe({next:r=>this.meta.set(r),error:e=>this.notice(readableError(e),true)});}}
 notice(msg:string,failed=false){this.message.set(msg);this.failed.set(failed);}
 batches(){return this.meta().batches.filter(b=>b.class_id===this.classId);}
 classChanged(){this.batchId=0;this.rows.set([]);}
 load(){this.message.set('');if(!this.batchId)return this.rows.set([]);
  const students=this.meta().students.filter(s=>s.batch_id===this.batchId);
  this.api.get<any>('attendance',{batch_id:this.batchId,date:this.attendanceDate}).subscribe({next:r=>{
   const existing=new Map(r.items.map((a:any)=>[a.student_id,a.status]));
   this.rows.set(students.map(s=>({student_id:s.id,name:s.name,code:s.code,status:(existing.get(s.id)||'') as Row['status']})));
  },error:e=>this.notice(readableError(e),true)});
 }
 allPresent(){this.rows.update(rows=>rows.map(r=>({...r,status:'present'})));}
 hasUnmarked(){return this.rows().some(r=>!r.status);}
 save(){if(!this.rows().length||!this.batchId)return;if(this.hasUnmarked()){this.notice('Mark attendance for all students before saving',true);return;}this.busy.set(true);
  this.api.post<any>('attendance/bulk',{batch_id:this.batchId,date:this.attendanceDate,records:this.rows().map(r=>({student_id:r.student_id,status:r.status}))}).subscribe({next:r=>{this.busy.set(false);this.notice(`Attendance saved for ${r.saved} students`);},error:e=>{this.busy.set(false);this.notice(readableError(e),true);}});
 }
}
