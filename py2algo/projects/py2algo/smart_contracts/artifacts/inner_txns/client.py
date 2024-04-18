# flake8: noqa
# fmt: off
# mypy: disable-error-code="no-any-return, no-untyped-call, misc, type-arg"
# This file was automatically generated by algokit-client-generator.
# DO NOT MODIFY IT BY HAND.
# requires: algokit-utils@^1.2.0
import base64
import dataclasses
import decimal
import typing
from abc import ABC, abstractmethod

import algokit_utils
import algosdk
from algosdk.v2client import models
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    AtomicTransactionResponse,
    SimulateAtomicTransactionResponse,
    TransactionSigner,
    TransactionWithSigner
)

_APP_SPEC_JSON = r"""{
    "hints": {
        "mint_nft()uint64": {
            "call_config": {
                "no_op": "CALL"
            }
        },
        "opt_in(asset)void": {
            "call_config": {
                "no_op": "CALL"
            }
        },
        "withdraw(uint64)void": {
            "call_config": {
                "no_op": "CALL"
            }
        }
    },
    "source": {
        "approval": "I3ByYWdtYSB2ZXJzaW9uIDEwCgpzbWFydF9jb250cmFjdHMuaW5uZXJfdHhucy5jb250cmFjdC5Jbm5lci5hcHByb3ZhbF9wcm9ncmFtOgogICAgdHhuIEFwcGxpY2F0aW9uSUQKICAgIGJueiBtYWluX2VudHJ5cG9pbnRAMgogICAgY2FsbHN1YiBfX2luaXRfXwoKbWFpbl9lbnRyeXBvaW50QDI6CiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weToyNAogICAgLy8gY2xhc3MgSW5uZXIoQVJDNENvbnRyYWN0KToKICAgIHR4biBOdW1BcHBBcmdzCiAgICBieiBtYWluX2JhcmVfcm91dGluZ0A5CiAgICBtZXRob2QgIm1pbnRfbmZ0KCl1aW50NjQiCiAgICBtZXRob2QgIm9wdF9pbihhc3NldCl2b2lkIgogICAgbWV0aG9kICJ3aXRoZHJhdyh1aW50NjQpdm9pZCIKICAgIHR4bmEgQXBwbGljYXRpb25BcmdzIDAKICAgIG1hdGNoIG1haW5fbWludF9uZnRfcm91dGVANCBtYWluX29wdF9pbl9yb3V0ZUA1IG1haW5fd2l0aGRyYXdfcm91dGVANgogICAgZXJyIC8vIHJlamVjdCB0cmFuc2FjdGlvbgoKbWFpbl9taW50X25mdF9yb3V0ZUA0OgogICAgLy8gc21hcnRfY29udHJhY3RzL2lubmVyX3R4bnMvY29udHJhY3QucHk6MzAKICAgIC8vIEBhcmM0LmFiaW1ldGhvZAogICAgdHhuIE9uQ29tcGxldGlvbgogICAgIQogICAgYXNzZXJ0IC8vIE9uQ29tcGxldGlvbiBpcyBOb09wCiAgICB0eG4gQXBwbGljYXRpb25JRAogICAgYXNzZXJ0IC8vIGlzIG5vdCBjcmVhdGluZwogICAgY2FsbHN1YiBtaW50X25mdAogICAgaXRvYgogICAgYnl0ZSAweDE1MWY3Yzc1CiAgICBzd2FwCiAgICBjb25jYXQKICAgIGxvZwogICAgaW50IDEKICAgIHJldHVybgoKbWFpbl9vcHRfaW5fcm91dGVANToKICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9pbm5lcl90eG5zL2NvbnRyYWN0LnB5OjQ0CiAgICAvLyBAYXJjNC5hYmltZXRob2QKICAgIHR4biBPbkNvbXBsZXRpb24KICAgICEKICAgIGFzc2VydCAvLyBPbkNvbXBsZXRpb24gaXMgTm9PcAogICAgdHhuIEFwcGxpY2F0aW9uSUQKICAgIGFzc2VydCAvLyBpcyBub3QgY3JlYXRpbmcKICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9pbm5lcl90eG5zL2NvbnRyYWN0LnB5OjI0CiAgICAvLyBjbGFzcyBJbm5lcihBUkM0Q29udHJhY3QpOgogICAgdHhuYSBBcHBsaWNhdGlvbkFyZ3MgMQogICAgYnRvaQogICAgdHhuYXMgQXNzZXRzCiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weTo0NAogICAgLy8gQGFyYzQuYWJpbWV0aG9kCiAgICBjYWxsc3ViIG9wdF9pbgogICAgaW50IDEKICAgIHJldHVybgoKbWFpbl93aXRoZHJhd19yb3V0ZUA2OgogICAgLy8gc21hcnRfY29udHJhY3RzL2lubmVyX3R4bnMvY29udHJhY3QucHk6NTcKICAgIC8vIEBhcmM0LmFiaW1ldGhvZAogICAgdHhuIE9uQ29tcGxldGlvbgogICAgIQogICAgYXNzZXJ0IC8vIE9uQ29tcGxldGlvbiBpcyBOb09wCiAgICB0eG4gQXBwbGljYXRpb25JRAogICAgYXNzZXJ0IC8vIGlzIG5vdCBjcmVhdGluZwogICAgLy8gc21hcnRfY29udHJhY3RzL2lubmVyX3R4bnMvY29udHJhY3QucHk6MjQKICAgIC8vIGNsYXNzIElubmVyKEFSQzRDb250cmFjdCk6CiAgICB0eG5hIEFwcGxpY2F0aW9uQXJncyAxCiAgICBidG9pCiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weTo1NwogICAgLy8gQGFyYzQuYWJpbWV0aG9kCiAgICBjYWxsc3ViIHdpdGhkcmF3CiAgICBpbnQgMQogICAgcmV0dXJuCgptYWluX2JhcmVfcm91dGluZ0A5OgogICAgLy8gc21hcnRfY29udHJhY3RzL2lubmVyX3R4bnMvY29udHJhY3QucHk6MjQKICAgIC8vIGNsYXNzIElubmVyKEFSQzRDb250cmFjdCk6CiAgICB0eG4gT25Db21wbGV0aW9uCiAgICAhCiAgICBhc3NlcnQgLy8gcmVqZWN0IHRyYW5zYWN0aW9uCiAgICB0eG4gQXBwbGljYXRpb25JRAogICAgIQogICAgYXNzZXJ0IC8vIGlzIGNyZWF0aW5nCiAgICBpbnQgMQogICAgcmV0dXJuCgoKLy8gc21hcnRfY29udHJhY3RzLmlubmVyX3R4bnMuY29udHJhY3QuSW5uZXIubWludF9uZnQoKSAtPiB1aW50NjQ6Cm1pbnRfbmZ0OgogICAgLy8gc21hcnRfY29udHJhY3RzL2lubmVyX3R4bnMvY29udHJhY3QucHk6MzAtMzEKICAgIC8vIEBhcmM0LmFiaW1ldGhvZAogICAgLy8gZGVmIG1pbnRfbmZ0KHNlbGYpIC0+IFVJbnQ2NDoKICAgIHByb3RvIDAgMQogICAgLy8gc21hcnRfY29udHJhY3RzL2lubmVyX3R4bnMvY29udHJhY3QucHk6MzcKICAgIC8vIHNlbGYuY291bnRlciArPSAxCiAgICBpbnQgMAogICAgYnl0ZSAiY291bnRlciIKICAgIGFwcF9nbG9iYWxfZ2V0X2V4CiAgICBhc3NlcnQgLy8gY2hlY2sgY291bnRlciBleGlzdHMKICAgIGludCAxCiAgICArCiAgICBieXRlICJjb3VudGVyIgogICAgc3dhcAogICAgYXBwX2dsb2JhbF9wdXQKICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9pbm5lcl90eG5zL2NvbnRyYWN0LnB5OjM5LTQwCiAgICAvLyBpdHhuLkFzc2V0Q29uZmlnKHRvdGFsPTEsIGRlY2ltYWxzPTAsIGFzc2V0X25hbWU9IkRPRyIsIHVuaXRfbmFtZT1iIkRPR18iICsgaXRvYShzZWxmLmNvdW50ZXIpLCBmZWU9MCkKICAgIC8vIC5zdWJtaXQoKQogICAgaXR4bl9iZWdpbgogICAgLy8gc21hcnRfY29udHJhY3RzL2lubmVyX3R4bnMvY29udHJhY3QucHk6MzkKICAgIC8vIGl0eG4uQXNzZXRDb25maWcodG90YWw9MSwgZGVjaW1hbHM9MCwgYXNzZXRfbmFtZT0iRE9HIiwgdW5pdF9uYW1lPWIiRE9HXyIgKyBpdG9hKHNlbGYuY291bnRlciksIGZlZT0wKQogICAgaW50IDAKICAgIGJ5dGUgImNvdW50ZXIiCiAgICBhcHBfZ2xvYmFsX2dldF9leAogICAgYXNzZXJ0IC8vIGNoZWNrIGNvdW50ZXIgZXhpc3RzCiAgICBjYWxsc3ViIGl0b2EKICAgIGJ5dGUgIkRPR18iCiAgICBzd2FwCiAgICBjb25jYXQKICAgIGludCAwCiAgICBpdHhuX2ZpZWxkIEZlZQogICAgaXR4bl9maWVsZCBDb25maWdBc3NldFVuaXROYW1lCiAgICBieXRlICJET0ciCiAgICBpdHhuX2ZpZWxkIENvbmZpZ0Fzc2V0TmFtZQogICAgaW50IDAKICAgIGl0eG5fZmllbGQgQ29uZmlnQXNzZXREZWNpbWFscwogICAgaW50IDEKICAgIGl0eG5fZmllbGQgQ29uZmlnQXNzZXRUb3RhbAogICAgaW50IGFjZmcKICAgIGl0eG5fZmllbGQgVHlwZUVudW0KICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9pbm5lcl90eG5zL2NvbnRyYWN0LnB5OjM5LTQwCiAgICAvLyBpdHhuLkFzc2V0Q29uZmlnKHRvdGFsPTEsIGRlY2ltYWxzPTAsIGFzc2V0X25hbWU9IkRPRyIsIHVuaXRfbmFtZT1iIkRPR18iICsgaXRvYShzZWxmLmNvdW50ZXIpLCBmZWU9MCkKICAgIC8vIC5zdWJtaXQoKQogICAgaXR4bl9zdWJtaXQKICAgIGl0eG4gQ3JlYXRlZEFzc2V0SUQKICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9pbm5lcl90eG5zL2NvbnRyYWN0LnB5OjM4LTQyCiAgICAvLyByZXR1cm4gKAogICAgLy8gICAgIGl0eG4uQXNzZXRDb25maWcodG90YWw9MSwgZGVjaW1hbHM9MCwgYXNzZXRfbmFtZT0iRE9HIiwgdW5pdF9uYW1lPWIiRE9HXyIgKyBpdG9hKHNlbGYuY291bnRlciksIGZlZT0wKQogICAgLy8gICAgIC5zdWJtaXQoKQogICAgLy8gICAgIC5jcmVhdGVkX2Fzc2V0LmlkCiAgICAvLyApCiAgICByZXRzdWIKCgovLyBzbWFydF9jb250cmFjdHMuaW5uZXJfdHhucy5jb250cmFjdC5pdG9hKG46IHVpbnQ2NCkgLT4gYnl0ZXM6Cml0b2E6CiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weTo2LTcKICAgIC8vIEBzdWJyb3V0aW5lCiAgICAvLyBkZWYgaXRvYShuOiBVSW50NjQsIC8pIC0+IEJ5dGVzOgogICAgcHJvdG8gMSAxCiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weToxNwogICAgLy8gYWNjID0gQnl0ZXMoKQogICAgYnl0ZSAiIgoKaXRvYV93aGlsZV90b3BAMToKICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9pbm5lcl90eG5zL2NvbnRyYWN0LnB5OjE4CiAgICAvLyB3aGlsZSBuID4gMDoKICAgIGZyYW1lX2RpZyAtMQogICAgYnogaXRvYV9hZnRlcl93aGlsZUAzCiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weToxOQogICAgLy8gYWNjID0gZGlnaXRzW24gJSAxMF0gKyBhY2MKICAgIGZyYW1lX2RpZyAtMQogICAgaW50IDEwCiAgICAlCiAgICBkdXAKICAgIGludCAxCiAgICArCiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weToxNgogICAgLy8gZGlnaXRzID0gQnl0ZXMoYiIwMTIzNDU2Nzg5IikKICAgIGJ5dGUgIjAxMjM0NTY3ODkiCiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weToxOQogICAgLy8gYWNjID0gZGlnaXRzW24gJSAxMF0gKyBhY2MKICAgIGNvdmVyIDIKICAgIHN1YnN0cmluZzMKICAgIGZyYW1lX2RpZyAwCiAgICBjb25jYXQKICAgIGZyYW1lX2J1cnkgMAogICAgLy8gc21hcnRfY29udHJhY3RzL2lubmVyX3R4bnMvY29udHJhY3QucHk6MjAKICAgIC8vIG4gLy89IDEwCiAgICBmcmFtZV9kaWcgLTEKICAgIGludCAxMAogICAgLwogICAgZnJhbWVfYnVyeSAtMQogICAgYiBpdG9hX3doaWxlX3RvcEAxCgppdG9hX2FmdGVyX3doaWxlQDM6CiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weToyMQogICAgLy8gcmV0dXJuIGFjYyBvciBCeXRlcyhiIjAiKQogICAgZnJhbWVfZGlnIDAKICAgIGxlbgogICAgYnogaXRvYV90ZXJuYXJ5X2ZhbHNlQDUKICAgIGZyYW1lX2RpZyAwCiAgICBiIGl0b2FfdGVybmFyeV9tZXJnZUA2CgppdG9hX3Rlcm5hcnlfZmFsc2VANToKICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9pbm5lcl90eG5zL2NvbnRyYWN0LnB5OjIxCiAgICAvLyByZXR1cm4gYWNjIG9yIEJ5dGVzKGIiMCIpCiAgICBieXRlICIwIgoKaXRvYV90ZXJuYXJ5X21lcmdlQDY6CiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weToyMQogICAgLy8gcmV0dXJuIGFjYyBvciBCeXRlcyhiIjAiKQogICAgc3dhcAogICAgcmV0c3ViCgoKLy8gc21hcnRfY29udHJhY3RzLmlubmVyX3R4bnMuY29udHJhY3QuSW5uZXIub3B0X2luKGFzc2V0OiB1aW50NjQpIC0+IHZvaWQ6Cm9wdF9pbjoKICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9pbm5lcl90eG5zL2NvbnRyYWN0LnB5OjQ0LTQ1CiAgICAvLyBAYXJjNC5hYmltZXRob2QKICAgIC8vIGRlZiBvcHRfaW4oc2VsZiwgYXNzZXQ6IEFzc2V0KSAtPiBOb25lOgogICAgcHJvdG8gMSAwCiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weTo1MS01NQogICAgLy8gaXR4bi5Bc3NldFRyYW5zZmVyKAogICAgLy8gICAgIGFzc2V0X3JlY2VpdmVyPUdsb2JhbC5jdXJyZW50X2FwcGxpY2F0aW9uX2FkZHJlc3MsCiAgICAvLyAgICAgeGZlcl9hc3NldD1hc3NldCwKICAgIC8vICAgICBmZWU9MCwKICAgIC8vICkuc3VibWl0KCkKICAgIGl0eG5fYmVnaW4KICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9pbm5lcl90eG5zL2NvbnRyYWN0LnB5OjUyCiAgICAvLyBhc3NldF9yZWNlaXZlcj1HbG9iYWwuY3VycmVudF9hcHBsaWNhdGlvbl9hZGRyZXNzLAogICAgZ2xvYmFsIEN1cnJlbnRBcHBsaWNhdGlvbkFkZHJlc3MKICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9pbm5lcl90eG5zL2NvbnRyYWN0LnB5OjU0CiAgICAvLyBmZWU9MCwKICAgIGludCAwCiAgICBpdHhuX2ZpZWxkIEZlZQogICAgZnJhbWVfZGlnIC0xCiAgICBpdHhuX2ZpZWxkIFhmZXJBc3NldAogICAgaXR4bl9maWVsZCBBc3NldFJlY2VpdmVyCiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weTo1MQogICAgLy8gaXR4bi5Bc3NldFRyYW5zZmVyKAogICAgaW50IGF4ZmVyCiAgICBpdHhuX2ZpZWxkIFR5cGVFbnVtCiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weTo1MS01NQogICAgLy8gaXR4bi5Bc3NldFRyYW5zZmVyKAogICAgLy8gICAgIGFzc2V0X3JlY2VpdmVyPUdsb2JhbC5jdXJyZW50X2FwcGxpY2F0aW9uX2FkZHJlc3MsCiAgICAvLyAgICAgeGZlcl9hc3NldD1hc3NldCwKICAgIC8vICAgICBmZWU9MCwKICAgIC8vICkuc3VibWl0KCkKICAgIGl0eG5fc3VibWl0CiAgICByZXRzdWIKCgovLyBzbWFydF9jb250cmFjdHMuaW5uZXJfdHhucy5jb250cmFjdC5Jbm5lci53aXRoZHJhdyhhbW91bnQ6IHVpbnQ2NCkgLT4gdm9pZDoKd2l0aGRyYXc6CiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weTo1Ny01OAogICAgLy8gQGFyYzQuYWJpbWV0aG9kCiAgICAvLyBkZWYgd2l0aGRyYXcoc2VsZiwgYW1vdW50OiBVSW50NjQpIC0+IE5vbmU6CiAgICBwcm90byAxIDAKICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9pbm5lcl90eG5zL2NvbnRyYWN0LnB5OjY0CiAgICAvLyBhc3NlcnQgVHhuLnNlbmRlciA9PSBHbG9iYWwuY3JlYXRvcl9hZGRyZXNzLCAiT25seSB0aGUgY3JlYXRvciBjYW4gd2l0aGRyYXciCiAgICB0eG4gU2VuZGVyCiAgICBnbG9iYWwgQ3JlYXRvckFkZHJlc3MKICAgID09CiAgICBhc3NlcnQgLy8gT25seSB0aGUgY3JlYXRvciBjYW4gd2l0aGRyYXcKICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9pbm5lcl90eG5zL2NvbnRyYWN0LnB5OjY1CiAgICAvLyBpdHhuLlBheW1lbnQocmVjZWl2ZXI9R2xvYmFsLmNyZWF0b3JfYWRkcmVzcywgYW1vdW50PWFtb3VudCwgZmVlPTApLnN1Ym1pdCgpCiAgICBpdHhuX2JlZ2luCiAgICBnbG9iYWwgQ3JlYXRvckFkZHJlc3MKICAgIGludCAwCiAgICBpdHhuX2ZpZWxkIEZlZQogICAgZnJhbWVfZGlnIC0xCiAgICBpdHhuX2ZpZWxkIEFtb3VudAogICAgaXR4bl9maWVsZCBSZWNlaXZlcgogICAgaW50IHBheQogICAgaXR4bl9maWVsZCBUeXBlRW51bQogICAgaXR4bl9zdWJtaXQKICAgIHJldHN1YgoKCi8vIHNtYXJ0X2NvbnRyYWN0cy5pbm5lcl90eG5zLmNvbnRyYWN0LklubmVyLl9faW5pdF9fKCkgLT4gdm9pZDoKX19pbml0X186CiAgICAvLyBzbWFydF9jb250cmFjdHMvaW5uZXJfdHhucy9jb250cmFjdC5weToyNwogICAgLy8gZGVmIF9faW5pdF9fKHNlbGYpIC0+IE5vbmU6CiAgICBwcm90byAwIDAKICAgIC8vIHNtYXJ0X2NvbnRyYWN0cy9pbm5lcl90eG5zL2NvbnRyYWN0LnB5OjI4CiAgICAvLyBzZWxmLmNvdW50ZXIgPSBVSW50NjQoMCkKICAgIGJ5dGUgImNvdW50ZXIiCiAgICBpbnQgMAogICAgYXBwX2dsb2JhbF9wdXQKICAgIHJldHN1Ygo=",
        "clear": "I3ByYWdtYSB2ZXJzaW9uIDEwCgpzbWFydF9jb250cmFjdHMuaW5uZXJfdHhucy5jb250cmFjdC5Jbm5lci5jbGVhcl9zdGF0ZV9wcm9ncmFtOgogICAgLy8gc21hcnRfY29udHJhY3RzL2lubmVyX3R4bnMvY29udHJhY3QucHk6MjQKICAgIC8vIGNsYXNzIElubmVyKEFSQzRDb250cmFjdCk6CiAgICBpbnQgMQogICAgcmV0dXJuCg=="
    },
    "state": {
        "global": {
            "num_byte_slices": 0,
            "num_uints": 1
        },
        "local": {
            "num_byte_slices": 0,
            "num_uints": 0
        }
    },
    "schema": {
        "global": {
            "declared": {
                "counter": {
                    "type": "uint64",
                    "key": "counter"
                }
            },
            "reserved": {}
        },
        "local": {
            "declared": {},
            "reserved": {}
        }
    },
    "contract": {
        "name": "Inner",
        "methods": [
            {
                "name": "mint_nft",
                "args": [],
                "returns": {
                    "type": "uint64",
                    "desc": "The asset ID of the NFT minted."
                },
                "desc": "Mints an NFT."
            },
            {
                "name": "opt_in",
                "args": [
                    {
                        "type": "asset",
                        "name": "asset",
                        "desc": "The asset to opt in to."
                    }
                ],
                "returns": {
                    "type": "void"
                },
                "desc": "Opts the application account in to receive an asset."
            },
            {
                "name": "withdraw",
                "args": [
                    {
                        "type": "uint64",
                        "name": "amount",
                        "desc": "The amount of MicroAlgos to withdraw."
                    }
                ],
                "returns": {
                    "type": "void"
                },
                "desc": "Transfers Algos to the application creator's account."
            }
        ],
        "networks": {},
        "desc": "A contract demonstrating inner transactions in algopy."
    },
    "bare_call_config": {
        "no_op": "CREATE"
    }
}"""
APP_SPEC = algokit_utils.ApplicationSpecification.from_json(_APP_SPEC_JSON)
_TReturn = typing.TypeVar("_TReturn")


class _ArgsBase(ABC, typing.Generic[_TReturn]):
    @staticmethod
    @abstractmethod
    def method() -> str:
        ...


_TArgs = typing.TypeVar("_TArgs", bound=_ArgsBase[typing.Any])


@dataclasses.dataclass(kw_only=True)
class _TArgsHolder(typing.Generic[_TArgs]):
    args: _TArgs


def _filter_none(value: dict | typing.Any) -> dict | typing.Any:
    if isinstance(value, dict):
        return {k: _filter_none(v) for k, v in value.items() if v is not None}
    return value


def _as_dict(data: typing.Any, *, convert_all: bool = True) -> dict[str, typing.Any]:
    if data is None:
        return {}
    if not dataclasses.is_dataclass(data):
        raise TypeError(f"{data} must be a dataclass")
    if convert_all:
        result = dataclasses.asdict(data)
    else:
        result = {f.name: getattr(data, f.name) for f in dataclasses.fields(data)}
    return _filter_none(result)


def _convert_transaction_parameters(
    transaction_parameters: algokit_utils.TransactionParameters | None,
) -> algokit_utils.TransactionParametersDict:
    return typing.cast(algokit_utils.TransactionParametersDict, _as_dict(transaction_parameters))


def _convert_call_transaction_parameters(
    transaction_parameters: algokit_utils.TransactionParameters | None,
) -> algokit_utils.OnCompleteCallParametersDict:
    return typing.cast(algokit_utils.OnCompleteCallParametersDict, _as_dict(transaction_parameters))


def _convert_create_transaction_parameters(
    transaction_parameters: algokit_utils.TransactionParameters | None,
    on_complete: algokit_utils.OnCompleteActionName,
) -> algokit_utils.CreateCallParametersDict:
    result = typing.cast(algokit_utils.CreateCallParametersDict, _as_dict(transaction_parameters))
    on_complete_enum = on_complete.replace("_", " ").title().replace(" ", "") + "OC"
    result["on_complete"] = getattr(algosdk.transaction.OnComplete, on_complete_enum)
    return result


def _convert_deploy_args(
    deploy_args: algokit_utils.DeployCallArgs | None,
) -> algokit_utils.ABICreateCallArgsDict | None:
    if deploy_args is None:
        return None

    deploy_args_dict = typing.cast(algokit_utils.ABICreateCallArgsDict, _as_dict(deploy_args))
    if isinstance(deploy_args, _TArgsHolder):
        deploy_args_dict["args"] = _as_dict(deploy_args.args)
        deploy_args_dict["method"] = deploy_args.args.method()

    return deploy_args_dict


@dataclasses.dataclass(kw_only=True)
class MintNftArgs(_ArgsBase[int]):
    """Mints an NFT."""

    @staticmethod
    def method() -> str:
        return "mint_nft()uint64"


@dataclasses.dataclass(kw_only=True)
class OptInArgs(_ArgsBase[None]):
    """Opts the application account in to receive an asset."""

    asset: int
    """The asset to opt in to."""

    @staticmethod
    def method() -> str:
        return "opt_in(asset)void"


@dataclasses.dataclass(kw_only=True)
class WithdrawArgs(_ArgsBase[None]):
    """Transfers Algos to the application creator's account."""

    amount: int
    """The amount of MicroAlgos to withdraw."""

    @staticmethod
    def method() -> str:
        return "withdraw(uint64)void"


class GlobalState:
    def __init__(self, data: dict[bytes, bytes | int]):
        self.counter = typing.cast(int, data.get(b"counter"))


@dataclasses.dataclass(kw_only=True)
class SimulateOptions:
    allow_more_logs: bool = dataclasses.field(default=False)
    allow_empty_signatures: bool = dataclasses.field(default=False)
    extra_opcode_budget: int = dataclasses.field(default=0)
    exec_trace_config: models.SimulateTraceConfig | None         = dataclasses.field(default=None)


class Composer:

    def __init__(self, app_client: algokit_utils.ApplicationClient, atc: AtomicTransactionComposer):
        self.app_client = app_client
        self.atc = atc

    def build(self) -> AtomicTransactionComposer:
        return self.atc

    def simulate(self, options: SimulateOptions | None = None) -> SimulateAtomicTransactionResponse:
        request = models.SimulateRequest(
            allow_more_logs=options.allow_more_logs,
            allow_empty_signatures=options.allow_empty_signatures,
            extra_opcode_budget=options.extra_opcode_budget,
            exec_trace_config=options.exec_trace_config,
            txn_groups=[]
        ) if options else None
        result = self.atc.simulate(self.app_client.algod_client, request)
        return result

    def execute(self) -> AtomicTransactionResponse:
        return self.app_client.execute_atc(self.atc)

    def mint_nft(
        self,
        *,
        transaction_parameters: algokit_utils.TransactionParameters | None = None,
    ) -> "Composer":
        """Mints an NFT.
        
        Adds a call to `mint_nft()uint64` ABI method
        
        :param algokit_utils.TransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :returns Composer: This Composer instance"""

        args = MintNftArgs()
        self.app_client.compose_call(
            self.atc,
            call_abi_method=args.method(),
            transaction_parameters=_convert_call_transaction_parameters(transaction_parameters),
            **_as_dict(args, convert_all=True),
        )
        return self

    def opt_in(
        self,
        *,
        asset: int,
        transaction_parameters: algokit_utils.TransactionParameters | None = None,
    ) -> "Composer":
        """Opts the application account in to receive an asset.
        
        Adds a call to `opt_in(asset)void` ABI method
        
        :param int asset: The asset to opt in to.
        :param algokit_utils.TransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :returns Composer: This Composer instance"""

        args = OptInArgs(
            asset=asset,
        )
        self.app_client.compose_call(
            self.atc,
            call_abi_method=args.method(),
            transaction_parameters=_convert_call_transaction_parameters(transaction_parameters),
            **_as_dict(args, convert_all=True),
        )
        return self

    def withdraw(
        self,
        *,
        amount: int,
        transaction_parameters: algokit_utils.TransactionParameters | None = None,
    ) -> "Composer":
        """Transfers Algos to the application creator's account.
        
        Adds a call to `withdraw(uint64)void` ABI method
        
        :param int amount: The amount of MicroAlgos to withdraw.
        :param algokit_utils.TransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :returns Composer: This Composer instance"""

        args = WithdrawArgs(
            amount=amount,
        )
        self.app_client.compose_call(
            self.atc,
            call_abi_method=args.method(),
            transaction_parameters=_convert_call_transaction_parameters(transaction_parameters),
            **_as_dict(args, convert_all=True),
        )
        return self

    def create_bare(
        self,
        *,
        on_complete: typing.Literal["no_op"] = "no_op",
        transaction_parameters: algokit_utils.CreateTransactionParameters | None = None,
    ) -> "Composer":
        """Adds a call to create an application using the no_op bare method
        
        :param typing.Literal[no_op] on_complete: On completion type to use
        :param algokit_utils.CreateTransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :returns Composer: This Composer instance"""

        self.app_client.compose_create(
            self.atc,
            call_abi_method=False,
            transaction_parameters=_convert_create_transaction_parameters(transaction_parameters, on_complete),
        )
        return self

    def clear_state(
        self,
        transaction_parameters: algokit_utils.TransactionParameters | None = None,
        app_args: list[bytes] | None = None,
    ) -> "Composer":
        """Adds a call to the application with on completion set to ClearState
    
        :param algokit_utils.TransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :param list[bytes] | None app_args: (optional) Application args to pass"""
    
        self.app_client.compose_clear_state(self.atc, _convert_transaction_parameters(transaction_parameters), app_args)
        return self


class InnerClient:
    """A contract demonstrating inner transactions in algopy.
    
    A class for interacting with the Inner app providing high productivity and
    strongly typed methods to deploy and call the app"""

    @typing.overload
    def __init__(
        self,
        algod_client: algosdk.v2client.algod.AlgodClient,
        *,
        app_id: int = 0,
        signer: TransactionSigner | algokit_utils.Account | None = None,
        sender: str | None = None,
        suggested_params: algosdk.transaction.SuggestedParams | None = None,
        template_values: algokit_utils.TemplateValueMapping | None = None,
        app_name: str | None = None,
    ) -> None:
        ...

    @typing.overload
    def __init__(
        self,
        algod_client: algosdk.v2client.algod.AlgodClient,
        *,
        creator: str | algokit_utils.Account,
        indexer_client: algosdk.v2client.indexer.IndexerClient | None = None,
        existing_deployments: algokit_utils.AppLookup | None = None,
        signer: TransactionSigner | algokit_utils.Account | None = None,
        sender: str | None = None,
        suggested_params: algosdk.transaction.SuggestedParams | None = None,
        template_values: algokit_utils.TemplateValueMapping | None = None,
        app_name: str | None = None,
    ) -> None:
        ...

    def __init__(
        self,
        algod_client: algosdk.v2client.algod.AlgodClient,
        *,
        creator: str | algokit_utils.Account | None = None,
        indexer_client: algosdk.v2client.indexer.IndexerClient | None = None,
        existing_deployments: algokit_utils.AppLookup | None = None,
        app_id: int = 0,
        signer: TransactionSigner | algokit_utils.Account | None = None,
        sender: str | None = None,
        suggested_params: algosdk.transaction.SuggestedParams | None = None,
        template_values: algokit_utils.TemplateValueMapping | None = None,
        app_name: str | None = None,
    ) -> None:
        """
        InnerClient can be created with an app_id to interact with an existing application, alternatively
        it can be created with a creator and indexer_client specified to find existing applications by name and creator.
        
        :param AlgodClient algod_client: AlgoSDK algod client
        :param int app_id: The app_id of an existing application, to instead find the application by creator and name
        use the creator and indexer_client parameters
        :param str | Account creator: The address or Account of the app creator to resolve the app_id
        :param IndexerClient indexer_client: AlgoSDK indexer client, only required if deploying or finding app_id by
        creator and app name
        :param AppLookup existing_deployments:
        :param TransactionSigner | Account signer: Account or signer to use to sign transactions, if not specified and
        creator was passed as an Account will use that.
        :param str sender: Address to use as the sender for all transactions, will use the address associated with the
        signer if not specified.
        :param TemplateValueMapping template_values: Values to use for TMPL_* template variables, dictionary keys should
        *NOT* include the TMPL_ prefix
        :param str | None app_name: Name of application to use when deploying, defaults to name defined on the
        Application Specification
            """

        self.app_spec = APP_SPEC
        
        # calling full __init__ signature, so ignoring mypy warning about overloads
        self.app_client = algokit_utils.ApplicationClient(  # type: ignore[call-overload, misc]
            algod_client=algod_client,
            app_spec=self.app_spec,
            app_id=app_id,
            creator=creator,
            indexer_client=indexer_client,
            existing_deployments=existing_deployments,
            signer=signer,
            sender=sender,
            suggested_params=suggested_params,
            template_values=template_values,
            app_name=app_name,
        )

    @property
    def algod_client(self) -> algosdk.v2client.algod.AlgodClient:
        return self.app_client.algod_client

    @property
    def app_id(self) -> int:
        return self.app_client.app_id

    @app_id.setter
    def app_id(self, value: int) -> None:
        self.app_client.app_id = value

    @property
    def app_address(self) -> str:
        return self.app_client.app_address

    @property
    def sender(self) -> str | None:
        return self.app_client.sender

    @sender.setter
    def sender(self, value: str) -> None:
        self.app_client.sender = value

    @property
    def signer(self) -> TransactionSigner | None:
        return self.app_client.signer

    @signer.setter
    def signer(self, value: TransactionSigner) -> None:
        self.app_client.signer = value

    @property
    def suggested_params(self) -> algosdk.transaction.SuggestedParams | None:
        return self.app_client.suggested_params

    @suggested_params.setter
    def suggested_params(self, value: algosdk.transaction.SuggestedParams | None) -> None:
        self.app_client.suggested_params = value

    def get_global_state(self) -> GlobalState:
        """Returns the application's global state wrapped in a strongly typed class with options to format the stored value"""

        state = typing.cast(dict[bytes, bytes | int], self.app_client.get_global_state(raw=True))
        return GlobalState(state)

    def mint_nft(
        self,
        *,
        transaction_parameters: algokit_utils.TransactionParameters | None = None,
    ) -> algokit_utils.ABITransactionResponse[int]:
        """Mints an NFT.
        
        Calls `mint_nft()uint64` ABI method
        
        :param algokit_utils.TransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :returns algokit_utils.ABITransactionResponse[int]: The asset ID of the NFT minted."""

        args = MintNftArgs()
        result = self.app_client.call(
            call_abi_method=args.method(),
            transaction_parameters=_convert_call_transaction_parameters(transaction_parameters),
            **_as_dict(args, convert_all=True),
        )
        return result

    def opt_in(
        self,
        *,
        asset: int,
        transaction_parameters: algokit_utils.TransactionParameters | None = None,
    ) -> algokit_utils.ABITransactionResponse[None]:
        """Opts the application account in to receive an asset.
        
        Calls `opt_in(asset)void` ABI method
        
        :param int asset: The asset to opt in to.
        :param algokit_utils.TransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :returns algokit_utils.ABITransactionResponse[None]: The result of the transaction"""

        args = OptInArgs(
            asset=asset,
        )
        result = self.app_client.call(
            call_abi_method=args.method(),
            transaction_parameters=_convert_call_transaction_parameters(transaction_parameters),
            **_as_dict(args, convert_all=True),
        )
        return result

    def withdraw(
        self,
        *,
        amount: int,
        transaction_parameters: algokit_utils.TransactionParameters | None = None,
    ) -> algokit_utils.ABITransactionResponse[None]:
        """Transfers Algos to the application creator's account.
        
        Calls `withdraw(uint64)void` ABI method
        
        :param int amount: The amount of MicroAlgos to withdraw.
        :param algokit_utils.TransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :returns algokit_utils.ABITransactionResponse[None]: The result of the transaction"""

        args = WithdrawArgs(
            amount=amount,
        )
        result = self.app_client.call(
            call_abi_method=args.method(),
            transaction_parameters=_convert_call_transaction_parameters(transaction_parameters),
            **_as_dict(args, convert_all=True),
        )
        return result

    def create_bare(
        self,
        *,
        on_complete: typing.Literal["no_op"] = "no_op",
        transaction_parameters: algokit_utils.CreateTransactionParameters | None = None,
    ) -> algokit_utils.TransactionResponse:
        """Creates an application using the no_op bare method
        
        :param typing.Literal[no_op] on_complete: On completion type to use
        :param algokit_utils.CreateTransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :returns algokit_utils.TransactionResponse: The result of the transaction"""

        result = self.app_client.create(
            call_abi_method=False,
            transaction_parameters=_convert_create_transaction_parameters(transaction_parameters, on_complete),
        )
        return result

    def clear_state(
        self,
        transaction_parameters: algokit_utils.TransactionParameters | None = None,
        app_args: list[bytes] | None = None,
    ) -> algokit_utils.TransactionResponse:
        """Calls the application with on completion set to ClearState
    
        :param algokit_utils.TransactionParameters transaction_parameters: (optional) Additional transaction parameters
        :param list[bytes] | None app_args: (optional) Application args to pass
        :returns algokit_utils.TransactionResponse: The result of the transaction"""
    
        return self.app_client.clear_state(_convert_transaction_parameters(transaction_parameters), app_args)

    def deploy(
        self,
        version: str | None = None,
        *,
        signer: TransactionSigner | None = None,
        sender: str | None = None,
        allow_update: bool | None = None,
        allow_delete: bool | None = None,
        on_update: algokit_utils.OnUpdate = algokit_utils.OnUpdate.Fail,
        on_schema_break: algokit_utils.OnSchemaBreak = algokit_utils.OnSchemaBreak.Fail,
        template_values: algokit_utils.TemplateValueMapping | None = None,
        create_args: algokit_utils.DeployCallArgs | None = None,
        update_args: algokit_utils.DeployCallArgs | None = None,
        delete_args: algokit_utils.DeployCallArgs | None = None,
    ) -> algokit_utils.DeployResponse:
        """Deploy an application and update client to reference it.
        
        Idempotently deploy (create, update/delete if changed) an app against the given name via the given creator
        account, including deploy-time template placeholder substitutions.
        To understand the architecture decisions behind this functionality please see
        <https://github.com/algorandfoundation/algokit-cli/blob/main/docs/architecture-decisions/2023-01-12_smart-contract-deployment.md>
        
        ```{note}
        If there is a breaking state schema change to an existing app (and `on_schema_break` is set to
        'ReplaceApp' the existing app will be deleted and re-created.
        ```
        
        ```{note}
        If there is an update (different TEAL code) to an existing app (and `on_update` is set to 'ReplaceApp')
        the existing app will be deleted and re-created.
        ```
        
        :param str version: version to use when creating or updating app, if None version will be auto incremented
        :param algosdk.atomic_transaction_composer.TransactionSigner signer: signer to use when deploying app
        , if None uses self.signer
        :param str sender: sender address to use when deploying app, if None uses self.sender
        :param bool allow_delete: Used to set the `TMPL_DELETABLE` template variable to conditionally control if an app
        can be deleted
        :param bool allow_update: Used to set the `TMPL_UPDATABLE` template variable to conditionally control if an app
        can be updated
        :param OnUpdate on_update: Determines what action to take if an application update is required
        :param OnSchemaBreak on_schema_break: Determines what action to take if an application schema requirements
        has increased beyond the current allocation
        :param dict[str, int|str|bytes] template_values: Values to use for `TMPL_*` template variables, dictionary keys
        should *NOT* include the TMPL_ prefix
        :param algokit_utils.DeployCallArgs | None create_args: Arguments used when creating an application
        :param algokit_utils.DeployCallArgs | None update_args: Arguments used when updating an application
        :param algokit_utils.DeployCallArgs | None delete_args: Arguments used when deleting an application
        :return DeployResponse: details action taken and relevant transactions
        :raises DeploymentError: If the deployment failed"""

        return self.app_client.deploy(
            version,
            signer=signer,
            sender=sender,
            allow_update=allow_update,
            allow_delete=allow_delete,
            on_update=on_update,
            on_schema_break=on_schema_break,
            template_values=template_values,
            create_args=_convert_deploy_args(create_args),
            update_args=_convert_deploy_args(update_args),
            delete_args=_convert_deploy_args(delete_args),
        )

    def compose(self, atc: AtomicTransactionComposer | None = None) -> Composer:
        return Composer(self.app_client, atc or AtomicTransactionComposer())