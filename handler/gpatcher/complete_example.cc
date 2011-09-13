
#include <windows.h>
#include <ah6x_hapi.h>
#include <ah6x_uapi.h>
#include <iostream>
#include <shlwapi.h>
#include <werapi.h>
#include "mini_disassembler.h"

typedef BOOL (WINAPI *pfnDispatchException)(PEXCEPTION_RECORD pExceptionRecord, PCONTEXT pContext);

#pragma section(".hooks", read, write, execute)
__declspec(allocate(".hooks")) BYTE OldDispatchException[AH6X_HAPI_SZ_APICALL];
__declspec(allocate(".hooks")) BYTE OldUnhandledExceptionFilter[AH6X_HAPI_SZ_APICALL];
#pragma comment(linker, "/SECTION:.hooks,RWE")

BOOL WINAPI DispatchExceptionHook(PEXCEPTION_RECORD pExceptionRecord, PCONTEXT pContext)
{
	std::wcout << "pContext@" << std::hex << (LONG)pContext << ", exception=(code=" << (LONG)pExceptionRecord << ", flags=" << pExceptionRecord->ExceptionFlags << ")" << std::endl;
	BOOL result = reinterpret_cast<pfnDispatchException>(&OldDispatchException)(pExceptionRecord, pContext);
	if (!(result&0x1)) {
		printf("Exception unhandled!\n");
		//std::wcout << "DispatchException: exception unhandled!" << std::endl;
		// todo: write dump
		// we cannot return from this method since there's no valid return value in case of unhandled exception
		// therefore the best thing to do is terminate the process
		::TerminateProcess(::GetCurrentProcess(), pExceptionRecord->ExceptionCode);
	}
	return result;
}

LONG __stdcall UnhandledExceptionFilterHook(PEXCEPTION_RECORD pExceptionRecord)
{
	printf("In UnhandledExceptionFilter!\n");
	// dummy filter
	return EXCEPTION_CONTINUE_SEARCH;
}

namespace {
	int a_ = 1;
	int foo() 
	{
		return 9+a_;
	}
	void fail()
	{
		__try {
			// f$%^&k!
			int a = foo();
			int b = a - 10;
			int p = *((int *)a);
		//} __except(EXCEPTION_EXECUTE_HANDLER) {
			// handled!
		}
		__finally {}
	}

	class dummy
	{
	public:
		dummy() {}
		~dummy() {}
	};

	BYTE lpRestoreBuffer[2][AH6X_HAPI_SZ_APISAVE];

	HRESULT setup_crash_handler()
	{
		using namespace sidestep;
		unsigned int displacement = 0;
		unsigned int bytes = 0, call_offset;
		InstructionType ins = IT_UNKNOWN;
		HMODULE hNative = ::GetModuleHandleW(L"ntdll.dll");

		PBYTE lpDispatcherFun = (PBYTE)::GetProcAddress(hNative, "KiUserExceptionDispatcher");
		//assert(lpDispatcherFun != NULL);
		std::wcout << "KiUserExceptionDispatcher@" << std::hex << (LONG)lpDispatcherFun << std::endl;

		MiniDisassembler mdis;
		while(ins != IT_JUMP && ins != IT_RETURN) {
			call_offset = bytes;
			ins = mdis.Disassemble(lpDispatcherFun+bytes, bytes);
			std::wcout << "instruction:" << std::hex << ins << ", bytes=" << bytes << std::endl;
		}
		//assert(IT_JUMP == ins);
		if (IT_JUMP == ins && 0xe8 == *(lpDispatcherFun+call_offset)) {
			displacement = *(DWORD*)(lpDispatcherFun+call_offset+1);
			LONG result = AH6X_HookApi(AH6X_HAPI_FL_OWR|AH6X_HAPI_FL_ADDRESS,
					(LPCWSTR)hNative,
					(LPCSTR)(lpDispatcherFun+bytes+displacement),
					lpRestoreBuffer[0],
					OldDispatchException,
					(LPBYTE)DispatchExceptionHook
					);
			if (AH6X_HAPI_RV_HOOKED != result) {
				std::wcerr << "Failed to hook, result=" << std::hex << result << std::endl;
				goto Error;
			}
			result = AH6X_HookApi(AH6X_HAPI_FL_OWR|AH6X_HAPI_FL_HMODULE,
					(LPCWSTR)::GetModuleHandleW(L"kernel32.dll"),
					"UnhandledExceptionFilter",
					lpRestoreBuffer[1],
					OldUnhandledExceptionFilter,
					(LPBYTE)UnhandledExceptionFilterHook
					);
			if (AH6X_HAPI_RV_HOOKED != result) {
				std::wcerr << "Failed to hook, result=" << std::hex << result << std::endl;
				// currently, fuck the possibly successfully hooked KiUserExceptionDispatcher! this is educational code!! 
				goto Error;
			}
			return S_OK;
		}
Error:
		return E_FAIL;
	}

	void unsetup_crash_handler()
	{
		// unhook only if no exception
		AH6X_UnhookApi(lpRestoreBuffer[0]);
		AH6X_UnhookApi(lpRestoreBuffer[1]);
	}

	HRESULT setup_crash_handler_wer()
	{
		HRESULT hr = E_FAIL;
		wchar_t crashHandlerHelperDllPath[MAX_PATH];
		if (::GetModuleFileName(NULL, crashHandlerHelperDllPath, MAX_PATH)>0 &&
			::PathRemoveFileSpec(crashHandlerHelperDllPath) &&
			::PathCombine(crashHandlerHelperDllPath, crashHandlerHelperDllPath, L"gwer.dll")) {
			hr = ::WerRegisterRuntimeExceptionModule(
					crashHandlerHelperDllPath,
					NULL	/*pContext*/
				);
		}
		return hr;
	}

	void unsetup_crash_handler_wer()
	{
		wchar_t crashHandlerHelperDllPath[MAX_PATH];
		if (::GetModuleFileName(NULL, crashHandlerHelperDllPath, MAX_PATH)>0 &&
			::PathRemoveFileSpec(crashHandlerHelperDllPath) &&
			::PathCombine(crashHandlerHelperDllPath, crashHandlerHelperDllPath, L"gwer.dll")) {
			// remove handler from WER
			::WerUnregisterRuntimeExceptionModule(
				crashHandlerHelperDllPath,
				NULL
			);
		}
	}

	void foobarbaz()
	{
		fail();
		throw dummy();
	}
}

int main(int argc, wchar_t const *argv[])
{
	argc, argv;

	setup_crash_handler_wer();
	foobarbaz();

	return 0;
}

